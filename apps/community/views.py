from django.views.generic import TemplateView, ListView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from .models import Post, Club, ClubMembership, ClubPost

class FeedView(ListView):
    model = Post
    template_name = 'community/feed.html'
    ordering = ['-created_at']
    paginate_by = 20

@method_decorator(login_required, name='dispatch')
class PostCreateView(CreateView):
    model = Post
    fields = ['text']
    template_name = 'community/post_form.html'
    success_url = reverse_lazy('community:feed')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ClubsView(ListView):
    model = Club
    template_name = 'community/clubs.html'

@login_required
def toggle_membership(request, pk):
    club = Club.objects.get(pk=pk)
    mem = ClubMembership.objects.filter(user=request.user, club=club)
    if mem.exists():
        mem.delete()
    else:
        ClubMembership.objects.create(user=request.user, club=club)
    return redirect('community:clubs')
