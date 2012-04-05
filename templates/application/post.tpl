{% extends "admin/base_site.html" %}
{% load i18n %}

{% block coltype %}colMS{% endblock %}
{% block adm_on %}{%endblock%}
{% block mod_on %}current{%endblock%}
{% block bodyclass %}dashboard{% endblock %}

{% block breadcrumbs %}
<div class="breadcrumbs">
    <a href="/application/">Home</a>
    &rsaquo; <a href='/application/show_model/{{model.id}}/'>{{model.name}}</a>
    &rsaquo; {{documento.title}}
</div>
{% endblock %}

{% block content %}
<script type='text/javascript'>
$(document).ready(function(){
    visible = false;
    $('.topicname').click(function(){
        $(this).next('.wordset').toggle('fast');
    });
});
</script>
<div id="content" class="colMS">
    <h1>{{model.name}}</h1>
    <h2>{{documento.title}}</h2>
    <div id='document'>
        <div class='categorias'>en {%for tag in prediction%} <div class='tag'>{{tag}}</div> {% endfor %}</div>
        {% if topicword %}
        <p><strong>Original Content</strong><br/><br/>{{documento.original_content}}</p>
        <p><strong>Cleaned Content</strong><br/><br/>{{documento.cleaned_content}}</p>
        <p><strong>Stemmed Content</strong><br/><br/>{{documento.steamed_content}}</p>
        <div class='black'>

        {% for key,twords in topicword %}
            <h3 class='topicname'>{{twords.name}} <b style='color:yellow'> {{twords.prediction_score}}% </b></h3>    
            <div class='wordset'>
                {% for k,v in twords.palabras.iteritems %}
                    <span class='keyword text-{{v}}'>{{k}}</span>
                {% endfor %}
            </div>
        {% endfor %}
        
        </div>
        {% else %}
        <p>No hay Topics!.</p>
        {% endif %}
    </div>
</div>
{% endblock %}








