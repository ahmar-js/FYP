
$(document).ready(function() {
    $('#Datarange1').on('input', function() {
      updateRange();
    });

    $('#Datarange2').on('input', function() {
      updateRange();
    });

    function updateRange() {
      var slider1Value = parseInt($('#Datarange1').val());
      var slider2Value = parseInt($('#Datarange2').val());

      if (slider1Value > slider2Value) {
        var temp = slider1Value;
        slider1Value = slider2Value;
        slider2Value = temp;
      }

      $('#Datarange1').val(slider1Value);
      $('#Datarange2').val(slider2Value);
    }
  });
