(function($, undefined) {
  // no dependencies, so let's add some utility functions:
  //
  // padzero: prepends 0, a classic.
  // from_time_str converts a time str into a time object
  // to_time_str converts a time object into a time str
  //   {hour: 13, minute: 45, second: 12} => '13:45:12'
  //   {hour: 9, minute: 9, second: 0} => '9:08:00'

  function padzero(val) {
    return (val < 10 ? '0' : '') + val;
  }

  var time_regex = /^(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?( ?[ap]\.?[m]\.?)?$/i;
  var now = new Date();
  var date = {
    hour: now.getHours(),
    minute: Math.round(now.getMinutes() / 15) * 15 % 60,
    second: 0
  };

  function default_time() {
    var output = {
      hour: date.hour,
      minute: date.minute,
      second: date.second
    };
    return output;
  }

  function from_time_str(input) {
    var match = input.match(time_regex);
    if ( ! match )
      return null;

    var output = {
      hour: date.hour,
      minute: date.minute,
      second: date.second
    };

    output.hour = parseInt(match[1], 10);
    output.minute = parseInt(match[2], 10);
    if ( match[3] )
      output.second = parseInt(match[3], 10);
    var is_pm;
    if ( match[4] )
      is_pm = match[4].match(/p/i);
    else
      is_pm = output.hour >= 12;

    if ( output.hour == 12 && ! is_pm )
      output.hour = 0;
    else if ( output.hour < 12 && is_pm )
      output.hour += 12;

    // corrections, errors default to 0 (or 12)
    if ( output.hour > 23 || output.hour < 0 )
      output.hour = 0;

    if ( output.minute > 59 || output.minute < 0 )
      output.minute = 0;

    if ( output.second > 59 || output.second < 0 )
      output.second = 0;
    return output;
  }

  function to_time_str(input) {
    var output = '';
    output += input.hour;

    output += ':';
    output += padzero(input.minute);

    if ( ! input.second )
      output += ':00';
    else
    {
      output += ':';
      output += padzero(input.second);
    }

    return output;
  }

  //|
  //|  event handlers
  //|
  //|  select_on_focus: when clicked or tabbed into, select the entire contents
  //|  up_down_ampm_event: responds to up, down, "a" and "p"
  //|  ampm_toggle_event: toggles am/pm, used as a trigger_stepper event
  //|  up_down_key_event: binds up and down to increment/decrement the value.
  //|  change_event: validates max and min
  //|  hour_change_event: validates max and min and rolls over am/pm
  //|  after_paste_event: parses the pasted string for a time string, and
  //|                     converts it to hour, minute, second, ampm
  //|  refresh_hidden_event: converts the time inputs to a time string and
  //|                        inserts it into the hidden input
  //|  focus_next_on_colon: a colon or space move the cursor to the next input
  //|  trigger_stepper: a mousedown event on the stepper triggers the "stepper"
  //|                   event on the focused input, or hour input if none have
  //|                   the focus
  //|  stepper_event: increments or decrements the focused input, triggered by
  //|                 clicking the stepper
  var up_key = 38, down_key = 40, tab_key = 9, colon_key = 186, space_key = 32;

  function select_on_focus(e) {
    $(this).select();
    if ( e.type == 'mousedown' )
      return false;
  }

  function ampm_toggle_event() {
    var assign = this.value.match(/a/i) ? 'pm' : 'am';
    $(this).val(assign).select().trigger('change');
    return false;
  }

  function up_down_ampm_event(e) {
    var assign;
    if ( e.which == up_key || e.which == down_key )
      assign = this.value.match(/a/i) ? 'pm' : 'am';
    else if ( e.which == 65 )
      assign = 'am';
    else if ( e.which == 80 )
      assign = 'pm';
    else if ( e.which == tab_key )
      return;
    else
      return false;

    $(this).val(assign).select().trigger('change');
    return false;
  }

  function up_down_key_event(e) {
    var current = parseInt(this.value, 10);
    if ( _.isNaN(current) )
      return;

    var step;
    if ( e.which == up_key )
      step = 1;
    else if ( e.which == down_key )
      step = -1;
    else
      return;

    // shift + up/down increments/decrements by 5
    step *= e.shiftKey ? 5 : 1;

    // add step
    current += step;

    // change value
    $(this).val(current).trigger('change', step);

    return false;
  }

  function generate_change_event(options, change_options) {
    var hidden_input = options.$hidden_input;

    _(change_options).defaults({
      min: null,
      max: null
    });

    function change_event() {
      var current = parseInt(this.value, 10);
      if ( _.isNaN(current) )
        return;

      if ( ! _.isNull(change_options.max) && current > change_options.max )
        current = change_options.max;

      if ( ! _.isNull(change_options.min) && current < change_options.min )
        current = change_options.min;

      // format value
      $(this).val(padzero(current.toString())).select();

      // refresh hidden input
      hidden_input.trigger('refresh_hidden');

      return false;
    }

    return change_event;
  }

  function generate_hour_change_event(options) {
    var hidden_input = options.$hidden_input;
    var ampm_input = options.$ampm_input;

    function toggle_ampm() {
      return ampm_toggle_event.apply(ampm_input[0]);
    }

    function hour_change_event(e, step) {
      var current = parseInt(this.value, 10);
      if ( _.isNaN(current) )
        return;

      var is_pm = ampm_input.val().match(/p/i);
      if ( step )
        if ( step > 0 && current == 12 && ! is_pm )  // step UP to 12 pm
          toggle_ampm();
        else if ( step < 0 && current == 11 && is_pm )
          toggle_ampm();
        else if ( step < 0 && current == 11 && ! is_pm )
          current = 12;

      if ( current > 12 )
        current = 1;
      if ( current > 11 && is_pm )
        current = 11;

      if ( current < 1 )
        current = 12;

      // format value
      $(this).val(current.toString()).select();

      // refresh hidden input
      hidden_input.trigger('refresh_hidden');

      return false;
    }
    return hour_change_event;
  }


  function generate_after_paste_event(options) {
    var hour_input = options.$hour_input;
    var minute_input = options.$minute_input;
    var second_input = options.$second_input;
    var ampm_input = options.$ampm_input;

    function after_paste_event() {
      if ( this.value.match(time_regex) )
      {
        var time = options.from_time_str(this.value);
        if ( ! time )
          return;

        options.quiet = true;
        var ampm, hour = time.hour;
        if ( time.hour >= 12 )
        {
          ampm = 'pm';
          if ( time.hour > 12 )
            hour -= 12;
        }
        else
        {
          ampm = 'am';
          if ( time.hour === 0 )
            hour = 12;
        }

        hour_input.val(hour);
        if ( minute_input )
          minute_input.val(time.minute);
        if ( second_input )
          second_input.val(time.second);
        ampm_input.val(ampm);
        options.quiet = false;

        return false;
      }
    }
    return after_paste_event;
  }

  function generate_refresh_hidden_event(options) {
    var hidden_input = options.$hidden_input;
    var hour_input = options.$hour_input;
    var minute_input = options.$minute_input;
    var second_input = options.$second_input;
    var ampm_input = options.$ampm_input;

    function refresh_hidden_event() {
      var time_str = '';
      time_str += hour_input.val();

      if ( minute_input )
        time_str += ':' + minute_input.val();
      else
        time_str += ':00';

      if ( second_input )
        time_str += ':' + second_input.val();

      time_str += ampm_input.val();

      var time = options.from_time_str(time_str);
      if ( time )
        hidden_input.val(options.to_time_str(time));
      else
        hidden_input.val();
      hidden_input.change();
    }
    return refresh_hidden_event;
  }

  function generate_focus_next_on_colon(options) {
    var listeners = options.listeners;
    var hidden_input = options.$hidden_input;

    function focus_next_on_colon(e) {
      if ( options.quiet )
        return false;

      if ( e.which == colon_key || e.which == space_key )
      {
        var current = $(listeners).index(this);
        current = (current + 1) % listeners.length;
        $(listeners[current]).focus();
        return false;
      }
    }
    return focus_next_on_colon;
  }

  //|
  //|  trigger event
  //|
  function generate_trigger_stepper(options) {
    var listeners = options.listeners;
    var hour_input = options.$hour_input;

    function trigger_stepper(e) {
      var focus_index;
      if ( $(':focus').length )
        focus_index = $(listeners).index($(':focus')[0]);
      else
        focus_index = -1;

      var focused;
      if ( focus_index == -1 )
        focused = hour_input;
      else
        focused = $(listeners[focus_index]);

      focused.trigger('stepper', e);
      return false;
    }
    return trigger_stepper;
  }

  function generate_stepper_event(options) {
    var listeners = options.listeners;
    var stepper = options.$stepper;

    function stepper_event(ignored, e) {
      var focused = $(this);
      var current = parseInt(focused.val(), 10);
      if ( _.isNaN(current) )
        return false;

      var mouse_offset = stepper.position();
      var mouse_y = e.pageY - mouse_offset.top;
      var step;
      if ( mouse_y > options.stepper_height )
      {
        step = -1;
        stepper.addClass(options.stepper_down_class);
      }
      else
      {
        step = 1;
        stepper.addClass(options.stepper_up_class);
      }

      if ( e.shiftKey )
        step *= 5;

      function increment_focused(pause) {
        if ( ! pause )
          pause = options.stepper_pause;
        current += step;
        focused.val(current.toString());
        focused.trigger('change', step);

        options.mouse_timer = window.setTimeout(increment_focused, pause);
      }
      increment_focused(options.stepper_initial_pause);

      stepper.focus();
      return false;
    }
    return stepper_event;
  }

  //|
  //|  the timeStepper plugin
  //|
  $.fn.timeStepper = function timeStepper(options) {
    var self = this;
    options = options || {};

    // assign defaults to options
    _(options).defaults($.fn.timeStepper.defaults);

    // assign private values
    options.mouse_timer = null;

    // start building replacement div and listeners array
    var replacement = $(options.el);
    var listeners = [];
    options.listeners = listeners;

    // the origin text input gets replaced with a hidden input
    // and an input for hours, minutes, seconds, and am/pm
    var hidden_input = this.hide();
    options.$hidden_input = hidden_input;

    var time = options.from_time_str(self.val());
    if ( ! time )
      time = default_time();

    // check options.resolution for "h" (hours only) or "s" (hours, minutes, and
    // seconds). all other values correspond to hours and minutes.
    var time_by_12 = (time.hour > 12 ? time.hour - 12 : (time.hour === 0 ? 12 : time.hour));
    var hour_input = $('<input type="text"/>').attr({
      'id': self.attr('id') + '-hour',
      'name': self.attr('name') + '-hour',
      'class': options.hour_class
    }).appendTo(replacement).val(time_by_12);

    listeners.push(hour_input[0]);
    options.$hour_input = hour_input;

    var minute_input;
    if ( options.resolution != 'h' )
    {
      $('<span>:</span>').attr('class', options.separator_class).appendTo(replacement);

      minute_input = $('<input type="text"/>').attr({
        'id': self.attr('id') + '-minute',
        'name': self.attr('name') + '-minute',
        'class': options.minute_class
      }).appendTo(replacement).val(padzero(time.minute));

      listeners.push(minute_input[0]);
    }
    options.$minute_input = minute_input;

    var second_input;
    if ( options.resolution == 's' )
    {
      $('<span>:</span>').attr('class', options.separator_class).appendTo(replacement);

      second_input = $('<input type="text"/>').attr({
        'id': self.attr('id') + '-second',
        'name': self.attr('name') + '-second',
        'class': options.second_class
      }).appendTo(replacement).val(padzero(time.second));

      listeners.push(second_input[0]);
    }
    options.$second_input = second_input;

    $('<span>&nbsp;</span>').attr('class', options.separator_class).appendTo(replacement);

    var ampm_input = $('<input type="text"/>').attr({
      'id': self.attr('id') + '-ampm',
      'name': self.attr('name') + '-ampm',
      'class': options.ampm_class
    }).appendTo(replacement).val(time.hour >= 12 ? 'pm' : 'am');

    listeners.push(ampm_input[0]);
    options.$ampm_input = ampm_input;

    var stepper = $('<span/>').attr('class', options.stepper_class).appendTo(replacement);
    options.$stepper = stepper;

    //|
    //|  bind event handlers
    //|
    hidden_input.on('refresh_hidden', generate_refresh_hidden_event(options));

    hour_input.on('keydown', up_down_key_event);
    hour_input.on('change', generate_hour_change_event(options));
    hour_input.on('stepper', generate_stepper_event(options));
    hour_input.on('keyup', generate_after_paste_event(options));

    if ( minute_input )
    {
      minute_input.on('keydown', up_down_key_event);
      minute_input.on('change', generate_change_event(options, { min: 0, max: 59, padzero: true}));
      minute_input.on('stepper', generate_stepper_event(options));
      minute_input.on('keyup', generate_after_paste_event(options));
    }

    if ( second_input )
    {
      second_input.on('keydown', up_down_key_event);
      second_input.on('change', generate_change_event(options, { min: 0, max: 59, padzero: true}));
      second_input.on('stepper', generate_stepper_event(options));
      second_input.on('keyup', generate_after_paste_event(options));
    }

    ampm_input.on('keydown', up_down_ampm_event);
    ampm_input.on('stepper', ampm_toggle_event);
    ampm_input.on('change', function() { hidden_input.trigger('refresh_hidden'); });
    ampm_input.on('keyup', generate_after_paste_event(options));

    stepper.on('mousedown', generate_trigger_stepper(options));

    $(document).on('mouseup', function() {
      if ( options.mouse_timer )
        window.clearTimeout(options.mouse_timer);
      options.mouse_timer = null;

      $(stepper).removeClass(options.stepper_up_class).removeClass(options.stepper_down_class);
    });

    self.after(replacement);

    //|
    //|  event handlers that get applied to all inputs
    //|
    _(listeners).each(function(listener) {
      $(listener).on('focus mousedown', select_on_focus);
      $(listener).on('keydown', generate_focus_next_on_colon(options));
    });

    return this;
  };

  $.fn.timeStepper.defaults = {
    from_time_str: from_time_str,
    to_time_str: to_time_str,

    // classes
    hidden_class: 'time',
    hour_class: 'hour',
    minute_class: 'minute',
    second_class: 'second',
    ampm_class: 'ampm',
    separator_class: 'separator',

    // stepper
    stepper_class: 'stepper',
    stepper_up_class: 'stepperUp',
    stepper_down_class: 'stepperDown',
    stepper_height: 13,
    stepper_initial_pause: 750,
    stepper_pause: 100,

    // resolution: {'h', 'm', 's'}
    // actually, only "h" or "s" are "valid" values, all other values
    // mean "minutes", the default resolution
    resolution: 'm',

    // wrapper class
    'el': '<div class="timeStepper"/>'
  };
})($);
