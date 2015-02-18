$(document).ready(function() {
    $("#btn_generate_cert").click(function(e){
       var post_url = $("#btn_generate_cert").data("endpoint");
       $('#btn_generate_cert').prop("disabled", true);
        $.ajax({
                 type: "POST",
                 url: post_url,
                 success: function (data) {
                    location.reload();
                   },
                 error: function(jqXHR, textStatus, errorThrown) {
                   var data = $.parseJSON(jqXHR.responseText);
                   $('#errors-info').html(data);
                   $('#btn_generate_cert').prop("disabled", false);
                 }
          });
    });
});