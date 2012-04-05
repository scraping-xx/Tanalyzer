{% extends "admin/base_site.html" %}
{% load i18n %}

{% block coltype %}colMS{% endblock %}
{% block adm_on %}{%endblock%}
{% block imp_on %}current{%endblock%}
{% block bodyclass %}dashboard{% endblock %}

{% block breadcrumbs %}
<div class="breadcrumbs">
    <a href="/application/">Home</a>
    &rsaquo; Classifier
</div>
{% endblock %}

{% block content %}
<script type='text/javascript'>
$(document).ready(function(){
	
	{% if success %}
	new Notification('{{success}}','success');
	{% endif %}

});
</script>

<div id="content" class="colMS">
	<br/>
	<form name='scrap' method = "post" action="" enctype="multipart/form-data">
		{% csrf_token %}
		<fieldset>
			<h2>Scrap Sites</h2>
			<table>
				<tr>
					<th colspan="2">Cargar datos a partir de los datasets de un modelo</th>
				</tr>
				<tr>
					<td>
						<label for='classifier'>Modelo</label>
					</td>
					<td>
						<select name='model'>
						{% for model in models %}
							<option value='{{model.id}}'>{{model.name}}</option>
						{% endfor %}
						</select>
					</td>
				</tr>
				<tr>
					<td>
						<label for='classifier'>Cantidad de Post</label>
					</td>
					<td>
						<input type='text' name='npost' size='3' />
					</td>
				</tr>
				<tr>
					<td colspan="2">
						<input type='hidden' name='form' value='scrap'>
						<a class='button' onClick="scrap.submit()" >Scrap!</a>
					</td>
				</tr>
			</table>
	    </fieldset>
	</form>
	<hr/>
	<form name="database" method="post" action="">
		{% csrf_token %}
		<fieldset class='fix-labels'>
			<h2>Carga desde base de datos</h2>
			<table>
				<tr>
					<th>Indicar los parámetros de conexión</th>
					<th>Indicar los campos en la base objetivo que representan los campos mencionados</th>
				</tr>
				<tr>
					<td>
						<label for='db_host'>Host*</label>
						<input type='text' name='db_host' value='msm.betazeta.com' /><br/>
						<label for='db_user'>User*</label>
						<input type='text' name='db_user' value='betazetanet' /><br/>
						<label for='db_pass'>Pass*</label>
						<input type='password' name='db_pass' value='betazetanet' /><br/>
						<label for='db_name'>Db Name*</label>
						<input type='text' name='db_name' value='stress0_bolido0' /><br/>
						<label for='db_table'>Table*</label>
						<input type='text' name='db_table' value='wp_posts' /><br/>
				    </td>
				    <td>
					    <label for='title'>Titulo*</label>
						<input type='text' name='title' value='post_title'/><br/>
						<label for='content'>Contenido*</label>
						<input type='text' name='content' value='post_content'/><br/>
						<label for='dataset'>
						Dataset*
						<a href="/admin/application/dataset/add/" class="add-another" id="add_id_client"> 
							<img src="/assets/admin/img/admin/icon_addlink.gif" width="10" height="10" alt="Add Another"/>
						</a>
						</label>
						<select name='dataset'>
							{% for dataset in datasets %}
							{% if dataset.id == 7 %}
							<option selected='selected' value="{{dataset.id}}">{{dataset.name}}</option>
							{% else %}
							<option value="{{dataset.id}}">{{dataset.name}}</option>
							{% endif %}
							{% endfor %}
						</select>

						<br/>
						<label for='url'>Url</label>
						<input type='text' name='url' /><br/>
						<label for='id'>Id Externo*</label>
						<input type='text' name='id' value='ID'/><br/>
						<label for='id'>Filtro Where</label>
						<input type='text' name='where' value='post_status = "publish"'/><br/>
				    </td>
			    </tr>
			    <tr>
			    	<td colspan='2'>
			    		<input type='hidden' name='form' value='database'>
					    <a class='button big' onClick="database.submit()" >Start!</a>
			    	</td>
			    </tr>
		    </table>
	    </fieldset>
	</form>
		
</div>

{% endblock %}











