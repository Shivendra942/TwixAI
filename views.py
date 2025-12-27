# ===================== Django Imports =====================
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

# ===================== App Imports =====================
from .models import Home
from .forms import TweetForm, UserRegistrationForm

# ===================== Gemini (NEW SDK) =====================
from google import genai
import os
import json

# Initialize Gemini client (NEW API)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ===================== BASIC VIEWS =====================
def index(request):
    return render(request, "index.html")


def tweet_list(request):
    tweets = Home.objects.all().order_by("-created_at")
    return render(request, "tweet_list.html", {"tweets": tweets})


# ===================== TWEET CRUD =====================
@login_required
def tweet_create(request):
    if request.method == "POST":
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            return redirect("tweet_list")
    else:
        form = TweetForm()
    return render(request, "tweet_form.html", {"form": form})


@login_required
def tweet_edit(request, tweet_id):
    tweet = get_object_or_404(Home, pk=tweet_id, user=request.user)

    if request.method == "POST":
        form = TweetForm(request.POST, request.FILES, instance=tweet)
        if form.is_valid():
            form.save()
            return redirect("tweet_list")
    else:
        form = TweetForm(instance=tweet)

    return render(request, "tweet_form.html", {"form": form})


@login_required
def tweet_delete(request, tweet_id):
    tweet = get_object_or_404(Home, pk=tweet_id, user=request.user)

    if request.method == "POST":
        tweet.delete()
        return redirect("tweet_list")

    return render(request, "tweet_confirm_delete.html", {"tweet": tweet})


# ===================== USER REGISTRATION =====================
def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.save()
            login(request, user)
            return redirect("tweet_list")
    else:
        form = UserRegistrationForm()

    return render(request, "registration/register.html", {"form": form})


# ===================== AI CHATBOT =====================
def gemini_chat_page(request):
    return render(request, "chatbot.html")


@csrf_exempt
def gemini_chat_api(request):
    if request.method != "POST":
        return JsonResponse({"reply": "Invalid request"}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()

        if not user_message:
            return JsonResponse({"reply": "Please type a message."})

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=user_message
        )

        return JsonResponse({"reply": response.text})

    except Exception as e:
        return JsonResponse({"reply": f"AI Error: {str(e)}"}, status=500)
