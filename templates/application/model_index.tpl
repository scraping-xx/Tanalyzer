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
    &rsaquo; Model Selection
</div>
{% endblock %}

{% block content %}
<script type='text/javascript'>
$(document).ready(function(){
    
    $('.button').click(function(){

        value = $(this).val();
        config = value;

        if (value == "Prepare!"){
            data = $('#prepare_form input,#prepare_form select').serialize()
            $("#prepare_form .loader").toggle('slow');
            $.ajax({url:'/ajax/prepare_data/?'+data, 
            dataType: 'json',
            success:
                function(data){
                    $("#prepare_form .loader").toggle('slow');
                    if (data.error){
                        new Notification(data.message, 'error');
                    }else{
                        new Notification(data.message, 'success');
                    }
                },
            error:
                function(data,stat,error){
                    $("#prepare_form .loader").toggle('slow');
                    if(!error) error = "SERVER NOT RUNNING?"
                    new Notification('There was an error: '+error, 'error');
                }
            });
        }
        if (value == "Train!" ){
            data = $('#train_form input,#train_form select').serialize()
            $("#train_form .loader").toggle('slow');
            $.ajax({url:'/ajax/train_data/?'+data, 
            dataType: 'json',
            success:
                function(data){
                    $("#train_form .loader").toggle('slow');
                    if (data.error){
                        new Notification(data.message, 'error');
                    }else{
                        new Notification(data.message, 'success');
                    }
                },
            error:
                function(data,stat,error){
                    $("#train_form .loader").toggle('slow');
                    if(!error) error = "SERVER NOT RUNNING?"
                    new Notification('There was an error: '+error, 'error');
                }
            });
        }
        if (value == "Show!"){
            return true;
        }
        if (value == "Asign!"){
            data = $('#asign_form input,#asign_form select').serialize()
            $("#asign_form .loader").toggle('slow');
            $.ajax({url:'/ajax/validation_data/?'+data, 
            dataType: 'json',
            success:
                function(data){
                    $("#asign_form .loader").toggle('slow');
                    if (data.error){
                        new Notification(data.message, 'error');
                    }else{
                        new Notification(data.message, 'success');
                    }
                },
            error:
                function(data,stat,error){
                    $("#asign_form .loader").toggle('slow');
                    if(!error) error = "SERVER NOT RUNNING?"
                    new Notification('There was an error: '+error, 'error');
                }
            });
        }

        return false;
    });

});
</script>

<div id="content" class="colMS">
<br/>
<h1>Mining Process</h1>
<br/>
{% if models %}
<table>
    <tr>
        <th>Prepare Data</th>
        <th>Set Validation Size</th>
        <th>Train</th>
        <th>Show</th>
    </tr>
    <tr>
        <td>
            <form id='prepare_form' method = "post" action="">
                {% csrf_token %}
                <fieldset>
                <label for='modelo'>Model</label><br/><br/>
                <select name='modelo'>
                    <option value='-1'>All</option>
                {% for model in models %}
                    <option value='{{model.id}}'>{{model.name}}</option>
                {% endfor %}
                </select>
                <br/>
                <input type='hidden' name='action' value='1'>
                <br/>
                <input type="submit" class='button' name="send" onClick='return false;' value="Prepare!">
                <span style='display:none' class='loader'><img src='/assets/admin/img/ajax-loader.gif' /></span>
                </fieldset>
            </form>
        </td>
        <td>
            <form id='asign_form' method = "post" action="">
                {% csrf_token %}
                <fieldset>
                <label for='modelo'>Model</label><br/><br/>
                <select name='modelo'>
                {% for model in models %}
                    <option value='{{model.id}}'>{{model.name}}</option>
                {% endfor %}
                </select>
                <br/><br/>
                <input class='mini' type='text' name='test_size' size='2' value='' placeholder='test% (1-100)'><br/>
                <input type='hidden' name='action' value='2'>
                <input type="submit" class='button' name="send" value="Asign!">
                <span style='display:none' class='loader'><img src='/assets/admin/img/ajax-loader.gif' /></span>
                </fieldset>
            </form>
        </td>
        <td>
            <form id='train_form' method = "post" action="">
                {% csrf_token %}
                <fieldset>
                <label for='modelo'>Model</label><br/><br/>
                <select name='modelo'>
                    <option value='-1'>All</option>
                {% for model in models %}
                    <option value='{{model.id}}'>{{model.name}}</option>
                {% endfor %}
                </select>
                <br/><br/>
                <input class='mini' type='text' name='alpha' size='2' value='' placeholder='Alpha (0.1)'><br/>
                <input class='mini' type='text' name='beta' size='2' value='' placeholder='Beta (1)'><br/>
                <input class='mini' type='text' name='ntopics' size='3' value='' placeholder='Número de Topics (15)'><br/>
                <input type='hidden' name='action' value='3'>
                <input type="submit" class='button' name="send" value="Train!">
                <span style='display:none' class='loader'><img src='/assets/admin/img/ajax-loader.gif' /></span>
                </fieldset>
            </form>
        </td>
        <td>
            <form name='show_form' method = "post" action="">
                {% csrf_token %}
                <fieldset>
                <label for='modelo'>Model</label><br/><br/>
                <select name='modelo'>
                {% for model in models %}
                    <option value='{{model.id}}'>{{model.name}}</option>
                {% endfor %}
                </select>
                <br/>
                <br/>
                <input type='hidden' name='action' value='4'>
                <input type="submit" class='button' name="send" value="Show!">
                <span style='display:none' class='loader'><img src='/assets/admin/img/ajax-loader.gif' /></span>
                </fieldset>
            </form>
        </td>
    </tr>
</table>

{% else %}
    <p>No hay Modelos!.</p>
{% endif %}
</div>

{% endblock %}









