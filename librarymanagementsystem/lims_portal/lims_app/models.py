from django.db import models
from django.conf import settings

# Create your models here.
class reader(models.Model):
  def __str__(self):
    return self.reader_name
  referance_id=models.CharField(max_length=200)
  reader_name=models.CharField(max_length=200)
  reader_contact=models.CharField(max_length=200)
  reader_address=models.TextField()
  active=models.BooleanField(default=True)


class Book(models.Model):
  CATEGORY_CHOICES = [
    ("Fiction", "Fiction"),
    ("Manga", "Manga"),
    ("Literature", "Literature"),
    ("Science", "Science"),
    ("Others", "Others"),
  ]

  title = models.CharField(max_length=255)
  author = models.CharField(max_length=255)
  category = models.CharField(max_length=32, choices=CATEGORY_CHOICES)
  isbn = models.CharField(max_length=32, unique=True)
  copies_available = models.PositiveIntegerField(default=0)

  def __str__(self):
    return f"{self.title} by {self.author}"


class Order(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  book = models.ForeignKey(Book, on_delete=models.CASCADE)
  quantity = models.PositiveIntegerField()
  ordered_at = models.DateTimeField(auto_now_add=True)
  returned = models.BooleanField(default=False)
  rental_duration_days = models.PositiveSmallIntegerField(default=14)
  is_confirmed = models.BooleanField(default=False)
  borrower_reference_id = models.CharField(max_length=200, blank=True)
  borrower_name = models.CharField(max_length=200, blank=True)

  def __str__(self):
    return f"{self.user} ordered {self.quantity} x {self.book}"

