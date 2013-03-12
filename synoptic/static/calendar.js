var SIZE_DECREMENT = 100;

$(document).ready(function() {
  var cal = $('#calendar');

  $.getJSON('/calendar/event_sources',
    function(event_sources) {
      var actual_event_sources = [];

      for (var i = 0; i<event_sources.length; ++i)
      {
        var entry = event_sources[i];
        if (!entry.requireOnline)
          actual_event_sources.push(entry);
        else
          if (window.navigator.onLine)
            actual_event_sources.push(entry);
      }

      cal.fullCalendar({
        theme: true,
        contentHeight: window.innerHeight-SIZE_DECREMENT,
        eventSources: actual_event_sources,
        header: {
          left: 'prev,next today',
          center: 'title',
          right: 'month,agendaWeek'
        }
      })
    });

  $(window).resize(function() {
    cal.fullCalendar('option', 'contentHeight', 
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
        cal.fullCalendar("refetchEvents");
        handled = true;
      }

      return !handled;
    });
});

