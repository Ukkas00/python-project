"""
URL configuration for lims_portal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('', home),
    path('home', home),
    path('Readers', reader_tab, name='reader_tab'),
    path('Books', books_view, name='books_view'),
    path('books', books_view, name='books_view_lower'),
    # Preferred slug route for My Bag
    path('my-bag', my_bag, name='my_bag'),
    # Backwards-compat alias (space in URL)
    path('My bag', my_bag, name='my_bag_legacy'),
    # Reader name lookup by Reference ID
    path('api/reader-lookup', reader_lookup, name='reader_lookup'),
    path('Returns', returns_view, name='returns_view'),
    path('save', save_student, name='save_student'),
    path('readers/add', save_reader, name='save_reader'),
    path('readers/<int:reader_id>/activate', activate_reader, name='activate_reader'),
    path('readers/<int:reader_id>/deactivate', deactivate_reader, name='deactivate_reader'),
]