import bleach
import markdown
import os

from django.forms import ModelForm, Textarea
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils import safestring
from django.views.decorators.csrf import csrf_exempt

import models
import settings

MIT_6_438_FILE = os.path.join(settings.CLIENT_SERVER_PATH, 'static', 'text', 'mit_6_438.txt')

BLEACH_TAG_WHITELIST = ['a', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul',
                        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']

def markdown_to_html(markdown_text):
    roadmap_html = markdown.markdown(markdown_text, safe_mode=True)
    return bleach.clean(roadmap_html, tags=BLEACH_TAG_WHITELIST)

    

def get_roadmap(request, username, roadmap_name):
    roadmap = models.load_roadmap(username, roadmap_name)
    if roadmap is None:
        return HttpResponse(status=404)

    if not roadmap.visible_to(request.user):
        return HttpResponse(status=404)
    
    can_edit = roadmap.editable_by(request.user)
    edit_url = '/roadmaps/%s/%s/edit' % (username, roadmap_name)

    # temporary: editing disabled on server
    if not settings.DEBUG:
        can_edit = False

    roadmap_html = markdown_to_html(roadmap.body)
    
    return render(request, 'roadmap.html', {
        'roadmap_html': safestring.mark_safe(roadmap_html),
        'title': roadmap.title,
        'author': roadmap.author,
        'audience': roadmap.audience,
        'show_edit_link': can_edit,
        'edit_url': edit_url,
        'CONTENT_SERVER': settings.CONTENT_SERVER,
        })


class RoadmapForm(ModelForm):
    class Meta:
        model = models.Roadmap
        fields = ('title', 'author', 'audience', 'visibility', 'body')
        widgets = {
            'body': Textarea(attrs={'cols': 100, 'rows': 40}),
            }

class RoadmapCreateForm(RoadmapForm):
    class Meta:
        model = models.Roadmap
        fields = ('title', 'url_tag', 'author', 'audience', 'visibility', 'body')
        widgets = {
            'body': Textarea(attrs={'cols': 100, 'rows': 40}),
            }
        

def edit_roadmap(request, username, roadmap_name):
    # temporary: editing disabled on server
    if not settings.DEBUG:
        return HttpResponse(status=404)
    
    if not request.user.is_authenticated():
        return HttpResponse(status=404)

    roadmap = models.load_roadmap(username, roadmap_name)
    if roadmap is None:
        return HttpResponse(status=404)
    if not roadmap.editable_by(request.user):
        return HttpResponse(status=404)
    
    if request.method == 'POST':
        form = RoadmapForm(request.POST, instance=roadmap)

        if form.is_valid():
            form.save()

            return HttpResponseRedirect('/roadmaps/%s/%s' % (username, roadmap_name))

    else:
        form = RoadmapForm(instance=roadmap)
    
    return render(request, 'roadmap-edit.html', {
        'form': form,
        'CONTENT_SERVER': settings.CONTENT_SERVER,
        })

def new_roadmap(request):
    # temporary: editing disabled on server
    if not settings.DEBUG:
        return HttpResponse(status=404)

    if not request.user.is_authenticated():
        return HttpResponse(status=404)

    if request.method == 'POST':
        form = RoadmapCreateForm(request.POST)
        if form.is_valid():
            roadmap = form.save(commit=False)
            roadmap.user = request.user
            roadmap.save()
            
            return HttpResponseRedirect('/roadmaps/%s/%s' % (request.user.username, roadmap.url_tag))
    else:
        form = RoadmapCreateForm()
        
    return render(request, 'roadmap-new.html', {
        'form': form,
        'CONTENT_SERVER': settings.CONTENT_SERVER,
        })


@csrf_exempt  # this is a POST request because it contains data, but there are no side effects
def preview_roadmap(request):
    if request.method != 'POST':
        return HttpResponse(status=404)

    title = request.POST['title'] if 'title' in request.POST else ''
    author = request.POST['author'] if 'author' in request.POST else ''
    audience = request.POST['audience'] if 'audience' in request.POST else ''
    body = request.POST['body'] if 'body' in request.POST else ''

    roadmap_html = markdown_to_html(body)
    
    return render(request, 'roadmap-content.html', {
        'title': title,
        'author': author,
        'audience': audience,
        'roadmap_html': safestring.mark_safe(roadmap_html),
        'show_edit_link': False,
        'CONTENT_SERVER': settings.CONTENT_SERVER,
        })


    