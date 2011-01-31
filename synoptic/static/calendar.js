var SIZE_DECREMENT = 90;

$(document).ready(function() {
  var cal =$('#calendar');

  cal.fullCalendar({
    theme: true,
    contentHeight: window.innerHeight-SIZE_DECREMENT,
    events: "/calendar/data",
    header: {
      left: 'title',
      center: 'today',
      right: 'month,agendaWeek prev,next'
    }
  })

  $(window).resize(function() {
    cal.fullCalendar('option', 'contentHeihgt', 
      window.innerHeight-SIZE_DECREMENT);
  });


  $(document).keypress(function(ev)
    {
      var key = String.fromCharCode(ev.charCode);
      var handled = false;

      if (key == "l")
      {
        cal.fullCalendar("next");
        handled = true;
      }
      if (key == "h")
      {
        cal.fullCalendar("prev");
        handled = true;
      }
      if (key == "m")
      {
        cal.fullCalendar("changeView", "month");
        handled = true;
      }
      if (key == "w")
      {
        cal.fullCalendar("changeView", "agendaWeek");
        handled = true;
      }
      if (key == "u")
      {
        // boo yuck
        cal.fullCalendar("prev");
        cal.fullCalendar("next");
        handled = true;
      }

      return !handled;
    });
});

