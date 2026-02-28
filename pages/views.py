from django.shortcuts import render
from .models import Category


def home(request):
	categories = Category.objects.filter(is_active=True)
	return render(request, "pages/home.html", {"categories": categories})
