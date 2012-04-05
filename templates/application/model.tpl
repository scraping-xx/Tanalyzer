{% extends "admin/base_site.html" %}
{% load i18n %}
{% block extrajs %}
	 <!-- Dajax -->
	{% load dajaxice_templatetags %} 
	{% dajaxice_js_import %}
	<script src="/assets/admin/js/jquery.dajax.core.js" type="text/javascript" charset="utf-8"></script>
{% endblock %}
{% block coltype %}colMS{% endblock %}
{% block adm_on %}{%endblock%}
{% block mod_on %}current{%endblock%}
{% block bodyclass %}dashboard{% endblock %}

{% block breadcrumbs %}
<div class="breadcrumbs">
    <a href="/application/">Home</a>
    &rsaquo; <a href='/application/show_model/{{model.id}}/'>Model</a>
    &rsaquo; {{model.name}}
</div>
{% endblock %}

{% block content %}

{% if topics %}
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["corechart"]});
      google.setOnLoadCallback(drawChart);
      function drawChart() {
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'Topic');
        data.addColumn('number', 'Porcentaje de artículos relacionados');
        data.addRows([
        {% for topic in topics %}
          ['{{topic.label}}',    {{topic.score|floatformat:1}}],
        {% endfor %}

        ]);

        var options = {
          title: 'Distribución temática para modelo {{model.name}}'
        };

        var chart = new google.visualization.PieChart(document.getElementById('chart_div'));
        chart.draw(data, options);

        $("#chart_container").toggle();

      }
    </script>
{% else %}
{% endif %}

<script type='text/javascript'>
$(document).ready(function(){



    $('html').on('click',function(){
        $('.original_topic_name').each(function(){
            cancel_edit($(this));
        });
    });

    $('.key a').click(function(){
        $(this).toggleClass("responseok");
        $(this).parent().parent().next().children().children('.keyset').toggle('fast');
        return false;
    });
    
    $('.dist a').click(function(){
        $(this).toggleClass("responseok");
        $(this).parent().parent().next().children().children('.distset').toggle('fast');
        return false;
    });

    $('.documents a').click(function(){
        $(this).toggleClass("responseok");
        $(this).parent().parent().next().children().children('.documentset').toggle('fast');
        return false;
    });

    $('.export a').click(function(){
        $(this).toggleClass("responseok");
        href = $(this).attr('href');
        $.getJSON(href,function(html){
            console.log(html.status);
            console.log(html.message)
          }
        );
        return false;
    });

    $('.topic_name').on("click",function(event){
        event.stopPropagation();
        toggle_editor($(this));
        return false;
    });

    $('#showchart').on("click",function(event){
        $("#chart_container").toggle("fast");
        return false;
    });

    $(".input_topic_name").live("keypress",function(event) {
        if(event.keyCode == 13){
            save($(this));
            cancel_edit($(this));
        }
    });
});

function toggle_editor(element){
    next = $(element).find('.input_topic_name').val();
    if (!next){
        label = $(element).html();
        input = "<input type='text' class='input_topic_name inline' name='topic_name' value='"+label+"'>";
        hidden = "<input type='hidden' class='original_topic_name' value='"+label+"'>";
        $(element).html(input+hidden);
    }
}

function cancel_edit(element){
	$(element).parent().html($(element).val())
}

function save(element){
	new_label = $(element).val();
    id = $(element).parent().parent().prev().html();

	$(element).html("Guardando...");
	Dajaxice.application.save_label(Dajax.process,{'new_label':new_label,'id':id});
}

</script>

<div id="content" class="colMS">
<br/>
<h1>Análisis de temas obtenidos para <strong>{{model.name}}</strong></h1>
<a href='/datamanager/import_master_topics/{{model.id}}/' class='button icon arrowright'>Inferir Labels</a>
<a href='' id='showchart' class='button'>Mostrar Distribución Temática</a>
<br/>
<div id='chart_container'>
    <div id="chart_div" style="width: 900; height: 500px; border: 10px solid #ccc; margin: 10px auto;"></div>
</div>
{% if topics %}
    {% for topic in topics %}
    <table style='width:100%;'>
    <tr>
        <th style='width: 20px;'>{{topic.id}}</th>
        <th style='width: 200px;'><span class='topic_name'>{{topic.label}}</span></th>
        <td class="points"> <b style='font-size:10px;'>Documentos Relacionados</b><br/> <strong> {{topic.get_percent_of_documents_related|floatformat:1}} % </strong></td>
        <td class="dist cursor"><a href='' class='button'>Ver Distribución</a></td>
        <td class="key cursor"><a href='' class='button'>Ver Keywords</a></td>
        <td class="documents cursor"><a href='' class='button'>Ver Titulares</a></td>
        <td class="export"><a href='/datamanager/export_master_topic/{{topic.id}}/' class='button icon add'>Exportar Topic</a></td>
    </tr>
    <tr>
        <td colspan="7" >

            <ul class='distribution distset' style="display:none" >
            {% for dataset in topic.tpl_dataset_relevance %}
                {% if dataset.percent|floatformat:0 < 30 %}
                <li title='{{dataset.value}}'>{{dataset.name}} <span class="percent">{{dataset.percent|floatformat:1}}%</span></li>
                {% else %}
                <li title='{{dataset.value}}'>{{dataset.name}} <span class="percent  important ">{{dataset.percent|floatformat:1}}%</span></li>
                {% endif %}
            {% endfor %}        
            </ul>
        
            <ul class='keyset' style='display:none'>
            {% for relation in topic.get_words %}
                <li class="word" title="{{relation.value}}">{{relation.word.name}}</li>
            {% endfor %}        
            </ul>
            
            <ul class="documentset" style="display:none" >
            {% for relation in topic.get_documents %}
                <li class='titulo_post' title="{{relation.value}}">
                <a class='button' href='/application/show_post/{{model.id}}/{{relation.document.id}}/'>
                {{relation.document.title}} 
                <span class="sitio">{{relation.document.dataset.name}}</span>
                </a>
                </li>
            {% endfor %}        
            </ul>
        </td>
    </tr>   
    </table>
    {% endfor %}
{% else %}
    <p>No hay Topics!.</p>
{% endif %}
</div>

{% endblock %}


