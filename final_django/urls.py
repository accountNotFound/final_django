"""final_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from .views import overview, search, example, traceback, xmind

urlpatterns = [
    path('top_refs', overview.get_top_refs),
    path('graph_queries', overview.post_graph_queries),
    path('cypher_queries', overview.post_cypher_queries),
    path('center_queries', overview.get_center_relations),
    path('abs_queries', search.post_abs_queries),
    path('tree_doc', search.get_tree_doc),
    path('traceback_example', example.traceback_example),
    path('traceback_check', traceback.post_traceback_check),
    path('xmind_source_expand', xmind.post_xmind_source_expand),
    path('xmind_target_query', xmind.post_xmind_target_query)
]
