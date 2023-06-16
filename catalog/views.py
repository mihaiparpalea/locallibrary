from django.shortcuts import render
from .models import Book, Author, BookInstance, Genre
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from catalog.forms import RenewBookForm
from django.views.generic.edit import CreateView, UpdateView, DeleteView
# from catalog.models import Author
import datetime


@login_required
def index(request):
	"""View function for home page of site."""

	# Generate counts of some of the main objects
	num_books = Book.objects.all().count()
	num_instances = BookInstance.objects.all().count()

	# Available books (status = 'a')
	num_instances_available = BookInstance.objects.filter(status__exact='a').count()

	# The 'all()' is implied by default.
	num_authors = Author.objects.count()
	num_genres = Genre.objects.count()
	num_word = Book.objects.filter(title__icontains='abație').count()

	# Number of visits to this view, as counted in the session variable.
	num_visits = request.session.get('num_visits', 0)
	request.session['num_visits'] = num_visits + 1

	context = {
		'num_books': num_books,
		'num_instances': num_instances,
		'num_instances_available': num_instances_available,
		'num_authors': num_authors,
		'num_genres': num_genres,
		'num_word': num_word,
		'num_visits': num_visits,
	}

	# Render the HTML template index.html with the data in the context variable
	return render(request, 'index.html', context=context)

class BookListView(LoginRequiredMixin, generic.ListView):
	model = Book
	paginate_by = 5

class BookDetailView(LoginRequiredMixin, generic.DetailView):
	model = Book

class BookCreate(PermissionRequiredMixin, CreateView):
	permission_required = 'catalog.add_book'
	model = Book
	fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']

class BookUpdate(PermissionRequiredMixin, UpdateView):
	permission_required = 'catalog.change_book'
	model = Book
	fields = '__all__' # Not recommended (potential security issue if more fields added)

class BookDelete(PermissionRequiredMixin, DeleteView):
	permission_required = 'catalog.delete_book'
	model = Book
	success_url = reverse_lazy('books')

class AuthorListView(LoginRequiredMixin, generic.ListView):
	model = Author
	paginate_by = 3

class AuthorDetailView(LoginRequiredMixin, generic.DetailView):
	model = Author

class AuthorCreate(PermissionRequiredMixin, CreateView):
	permission_required = 'catalog.add_author'
	model = Author
	fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
	permission_required = 'catalog.change_author'
	model = Author
	fields = '__all__' # Not recommended (potential security issue if more fields added)

class AuthorDelete(PermissionRequiredMixin, DeleteView):
	permission_required = 'catalog.delete_author'
	model = Author
	success_url = reverse_lazy('authors')

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
	"""Generic class-based view listing books on loan to current user."""
	model = BookInstance
	template_name = 'catalog/bookinstance_list_borrowed_user.html'
	paginate_by = 3

	def get_queryset(self):
		return (
			BookInstance.objects.filter(borrower=self.request.user)
			.filter(status__exact='o')
			.order_by('due_back')
		)

class LoanedBooksListView(PermissionRequiredMixin, generic.ListView):
	"""Generic class-based view listing books on loan to current user."""
	permission_required = 'catalog.can_mark_returned'
	model = BookInstance
	template_name = 'catalog/bookinstance_list_borrowed.html'
	paginate_by = 5

	def get_queryset(self):
		return (
			BookInstance.objects.filter(status__exact='o')
			.order_by('due_back')
		)

@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
	"""View function for renewing a specific BookInstance by librarian."""
	book_instance = get_object_or_404(BookInstance, pk=pk)

	# If this is a POST request then process the Form data
	if request.method == 'POST':

		# Create a form instance and populate it with data from the request (binding):
		form = RenewBookForm(request.POST)

		# Check if the form is valid:
		if form.is_valid():
			# process the data in form.cleaned_data as required (here we just write it to the model due_back field)
			book_instance.due_back = form.cleaned_data['renewal_date']
			book_instance.save()

			# redirect to a new URL:
			return HttpResponseRedirect(reverse('all-borrowed'))

	# If this is a GET (or any other method) create the default form.
	else:
		proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
		form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

	context = {
		'form': form,
		'book_instance': book_instance,
	}

	return render(request, 'catalog/book_renew_librarian.html', context)
