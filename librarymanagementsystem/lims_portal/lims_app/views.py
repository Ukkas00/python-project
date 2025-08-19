from django.shortcuts import render
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

# Create your views here.
from .models import reader, Book, Order


def home(request):
    return render(request,'home.html', context={"current_tab": "home"})

def Readers(request):
    return render(request,'Readers.html', context={"current_tab": "Readers"})

def shopping (request):
    return HttpResponse("welcome to shopping")

def save_student(request):
    if request.method == "POST":
        student_name = request.POST.get('student_name', '')
        # Here you would typically save the student_name to the database or perform other logic
        # For now, just return a simple response
        return render(request, 'welcome.html', context={'student_name': student_name})

def reader_tab(request):
    if request.method == "POST":
        query = request.POST.get('query', '').strip()
        if query:
            readers_list = reader.objects.filter(reader_name__icontains=query)
        else:
            readers_list = reader.objects.all()
    else:
        readers_list = reader.objects.all()
    return render(request, "Readers.html", context={"current_tab": "Readers", "readers": readers_list})

def save_reader(request):
    if request.method == "POST":
        reader_name = request.POST.get('Reader_name', '')
        referance_id = request.POST.get('Reference ID', '')
        reader_contact = request.POST.get('Reader_Contact', '')
        reader_address = request.POST.get('Reader_Address', '')

        reader_item = reader(
            reader_name=reader_name,
            referance_id=referance_id,
            reader_contact=reader_contact,
            reader_address=reader_address,
            active=True
        )
        reader_item.save()
        return redirect('/Readers')

def activate_reader(request, reader_id):
    if request.method == "POST":
        target_reader = get_object_or_404(reader, id=reader_id)
        target_reader.active = True
        target_reader.save()
    return redirect('/Readers')

def deactivate_reader(request, reader_id):
    if request.method == "POST":
        target_reader = get_object_or_404(reader, id=reader_id)
        target_reader.active = False
        target_reader.save()
    return redirect('/Readers')

def books_view(request):
    create_error = None
    create_success = None

    # Handle create-book submission (manual add)
    if request.method == "POST" and request.POST.get("action") == "create_book":
        title = (request.POST.get("title") or "").strip()
        author = (request.POST.get("author") or "").strip()
        category = (request.POST.get("category") or "").strip()
        isbn = (request.POST.get("isbn") or "").strip()
        copies_str = (request.POST.get("copies_available") or "0").strip()
        try:
            copies_available = max(0, int(copies_str))
        except ValueError:
            copies_available = 0

        allowed_categories = {c for c, _ in Book.CATEGORY_CHOICES}
        if not title or not author or not isbn:
            create_error = "Title, author, and ISBN are required."
        elif category not in allowed_categories:
            create_error = "Invalid category."
        elif Book.objects.filter(isbn=isbn).exists():
            create_error = "ISBN already exists."
        else:
            Book.objects.create(
                title=title,
                author=author,
                category=category,
                isbn=isbn,
                copies_available=copies_available,
            )
            create_success = "Book added successfully."

    # Handle add-to-bag submission
    if request.method == "POST" and request.POST.get("action") == "add_to_bag":
        book_id = request.POST.get("book_id")
        quantity_str = request.POST.get("quantity", "1")
        try:
            quantity = max(1, int(quantity_str))
        except ValueError:
            quantity = 1

        target_book = Book.objects.filter(id=book_id).first()
        if not request.user.is_authenticated:
            create_error = "Please sign in to add books to your bag."
        elif not target_book:
            create_error = "Book not found."
        elif target_book.copies_available < quantity:
            create_error = "Not enough copies available."
        else:
            Order.objects.create(
                user=request.user,
                book=target_book,
                quantity=quantity,
                returned=False,
            )
            target_book.copies_available -= quantity
            target_book.save()
            # After successful add, go to My Bag
            return redirect('/my-bag')

    # Searching by title or author
    query = (request.GET.get("q") or request.POST.get("q") or "").strip()
    if query:
        books = Book.objects.filter(Q(title__icontains=query) | Q(author__icontains=query)).order_by("title")
    else:
        books = Book.objects.all().order_by("title")

    # Count distinct titles (not copies)
    total_titles = Book.objects.values("title").distinct().count()

    return render(request, "Books.html", context={
        "current_tab": "Books",
        "books": books,
        "q": query,
        "create_error": create_error,
        "create_success": create_success,
        "total_titles": total_titles,
    })

def my_bag(request):
    form_error = None
    form_success = None

    # User's pending orders (not confirmed yet)
    bag_items = Order.objects.filter(user=request.user, is_confirmed=False).select_related("book").order_by("-ordered_at")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "set_duration":
            order_id = request.POST.get("order_id")
            duration_str = request.POST.get("rental_duration", "14")
            try:
                duration = int(duration_str)
            except ValueError:
                duration = 14
            if duration not in (7, 14, 21):
                duration = 14
            Order.objects.filter(id=order_id, user=request.user, is_confirmed=False).update(rental_duration_days=duration)
        elif action == "remove_item":
            order_id = request.POST.get("order_id")
            order = Order.objects.filter(id=order_id, user=request.user, is_confirmed=False).select_related("book").first()
            if order:
                # Return copies back to availability
                order.book.copies_available += order.quantity
                order.book.save()
                order.delete()
        elif action == "lookup_reader":
            # Just resolve and display the reader name; no state changes
            pass
        elif action == "confirm_rental":
            referance_id = (request.POST.get("referance_id") or "").strip()
            if not bag_items.exists():
                form_error = "Your bag is empty."
            elif not referance_id:
                form_error = "Reference ID is required to borrow."
            else:
                linked_reader = reader.objects.filter(referance_id=referance_id).first()
                if not linked_reader:
                    form_error = "Reference ID not found."
                elif not linked_reader.active:
                    form_error = "Reader is inactive and cannot borrow."
                else:
                    # stamp borrower info on all items then confirm
                    for o in bag_items:
                        o.borrower_reference_id = referance_id
                        o.borrower_name = linked_reader.reader_name
                        o.is_confirmed = True
                        o.save()
                    form_success = "Rental confirmed. Enjoy your books!"

        # Requery after changes
        bag_items = Order.objects.filter(user=request.user, is_confirmed=False).select_related("book").order_by("-ordered_at")

    # If a referance_id is present, resolve name
    referance_id = (
        request.POST.get("referance_id")
        if request.method == "POST"
        else request.GET.get("referance_id", "")
    ) or ""
    reader_name = ""
    reader_id = None
    if referance_id:
        r = reader.objects.filter(referance_id=referance_id).first()
        if r:
            reader_name = r.reader_name
            reader_id = r.id

    return render(request, "my_bag.html", {
        "current_tab": "My bag",
        "bag_items": bag_items,
        "referance_id": referance_id,
        "reader_name": reader_name,
        "reader_id": reader_id,
        "form_error": form_error,
        "form_success": form_success,
    })


def reader_lookup(request):
    """Return reader name and internal ID for a given external Reference ID.

    This treats Reference ID (external) as distinct from the reader's internal primary key.
    """
    ref = (request.GET.get("referance_id") or request.GET.get("reference_id") or "").strip()
    result = {"name": "", "reader_id": None, "found": False}
    if ref:
        r = reader.objects.filter(referance_id=ref, active=True).first()
        if r:
            result.update({
                "name": r.reader_name,
                "reader_id": r.id,
                "found": True,
            })
    return JsonResponse(result)


def returns_view(request):
    form_error = None
    form_success = None

    if request.method == "POST" and request.POST.get("action") == "mark_returned":
        order_id = request.POST.get("order_id")
        order = (
            Order.objects.filter(id=order_id, returned=False, is_confirmed=True)
            .select_related("book")
            .first()
        )
        if not order:
            form_error = "Order not found."
        else:
            # increment stock and mark returned
            order.book.copies_available += order.quantity
            order.book.save()
            order.returned = True
            order.save()
            form_success = "Marked as returned."

    active_orders = list(
        Order.objects.filter(is_confirmed=True, returned=False)
        .select_related("book", "user")
        .order_by("-ordered_at")
    )
    # compute due date for each
    for o in active_orders:
        o.due_date = o.ordered_at + timedelta(days=(o.rental_duration_days or 14))

    return render(request, "returns.html", {
        "current_tab": "Returns",
        "orders": active_orders,
        "form_error": form_error,
        "form_success": form_success,
    })

