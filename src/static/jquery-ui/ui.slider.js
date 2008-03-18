(function($) {

	$.fn.extend({
		slider: function(options) {
			var args = Array.prototype.slice.call(arguments, 1);
			
			if ( options == "value" )
				return $.data(this[0], "slider").value(arguments[1]);
			
			return this.each(function() {
				if (typeof options == "string") {
					var slider = $.data(this, "slider");
					if (slider) slider[options].apply(slider, args);

				} else if(!$.data(this, "slider"))
					new $.ui.slider(this, options);
			});
		}
	});
	
	$.ui.slider = function(element, options) {

		//Initialize needed constants
		var self = this;
		this.element = $(element);
		$.data(element, "slider", this);
		this.element.addClass("ui-slider");
		
		//Prepare the passed options
		this.options = $.extend({}, $.ui.slider.defaults, options);
		var o = this.options;
		$.extend(o, {
			axis: o.axis || (element.offsetWidth < element.offsetHeight ? 'vertical' : 'horizontal'),
			maxValue: !isNaN(parseInt(o.maxValue,10)) ? parseInt(o.maxValue, 10) :  100,
			minValue: parseInt(o.minValue,10) || 0
		});
		
		//Prepare the real maxValue
		o.realMaxValue = o.maxValue - o.minValue;
		
		//Calculate stepping based on steps
		o.stepping = parseInt(o.stepping, 10) || (o.steps ? o.realMaxValue/o.steps : 0);
		
		$(element).bind("setData.slider", function(event, key, value){
			self.options[key] = value;
		}).bind("getData.slider", function(event, key){
			return self.options[key];
		});

		//Initialize mouse and key events for interaction
		this.handle = $(o.handle, element);
		if (!this.handle.length) {
			self.handle = self.generated = $(o.handles || [0]).map(function() {
				var handle = $("<div/>").addClass("ui-slider-handle").appendTo(element);
				if (this.id)
					handle.attr("id", this.id);
				return handle[0];
			});
		}
		$(this.handle)
			.mouseInteraction({
				executor: this,
				delay: o.delay,
				distance: o.distance || 0,
				dragPrevention: o.prevention ? o.prevention.toLowerCase().split(',') : ['input','textarea','button','select','option'],
				start: this.start,
				stop: this.stop,
				drag: this.drag,
				condition: function(e, handle) {
					if(!this.disabled) {
						if(this.currentHandle) this.blur(this.currentHandle);
						this.focus(handle,1);
						return !this.disabled;
					}
				}
			})
			.wrap('<a href="javascript:void(0)"></a>')
			.parent()
				.bind('focus', function(e) { self.focus(this.firstChild); })
				.bind('blur', function(e) { self.blur(this.firstChild); })
				.bind('keydown', function(e) {
					if(/(37|39)/.test(e.keyCode)) {
						self.moveTo((e.keyCode == 37 ? '-' : '+') + '=' + self.oneStep(),this.firstChild);
					}
				})
		;
		
		//Position the node
		if(o.helper == 'original' && (this.element.css('position') == 'static' || this.element.css('position') == '')) this.element.css('position', 'relative');
		
		//Prepare dynamic properties for later use
		if(o.axis == 'horizontal') {
			this.size = this.element.outerWidth();
			this.properties = ['left', 'width'];
		} else {
			this.size = this.element.outerHeight();
			this.properties = ['top', 'height'];
		}
		
		//Bind the click to the slider itself
		this.element.bind('click.slider', function(e) { self.click.apply(self, [e]); });
		
		//Move the first handle to the startValue
		$.each(o.handles || [], function(index, handle) {
			self.moveTo(handle.start, index, true);
		});
		if (!isNaN(o.startValue))
			this.moveTo(o.startValue, 0, true);
		
		//If we only have one handle, set the previous handle to this one to allow clicking before selecting the handle
		if(this.handle.length == 1) this.previousHandle = this.handle;
		
		
		if(this.handle.length == 2 && o.range) this.createRange();
	
	};
	
	$.extend($.ui.slider.prototype, {
		plugins: {},
		createRange: function() {
			this.rangeElement = $('<div></div>')
				.addClass('ui-slider-range')
				.css({ position: 'absolute' })
				.appendTo(this.element);
			this.updateRange();
		},
		updateRange: function() {
				this.rangeElement.css(this.properties[0], parseInt($(this.handle[0]).css(this.properties[0]),10) + this.handleSize(0)/2);
				this.rangeElement.css(this.properties[1], parseInt($(this.handle[1]).css(this.properties[0]),10) - parseInt($(this.handle[0]).css(this.properties[0]),10));
		},
		getRange: function() {
			return this.rangeElement ? this.convertValue(parseInt(this.rangeElement.css(this.properties[1]),10)) : null;
		},
		ui: function(e) {
			return {
				instance: this,
				options: this.options,
				handle: this.currentHandle,
				value: this.value(),
				range: this.getRange()
			};
		},
		propagate: function(n,e) {
			$.ui.plugin.call(this, n, [e, this.ui()]);
			this.element.triggerHandler(n == "slide" ? n : "slide"+n, [e, this.ui()], this.options[n]);
		},
		destroy: function() {
			this.element
				.removeClass("ui-slider ui-slider-disabled")
				.removeData("slider")
				.unbind(".slider");
			this.handle.removeMouseInteraction();
			this.generated && this.generated.remove();
		},
		enable: function() {
			this.element.removeClass("ui-slider-disabled");
			this.disabled = false;
		},
		disable: function() {
			this.element.addClass("ui-slider-disabled");
			this.disabled = true;
		},
		focus: function(handle,hard) {
			this.currentHandle = $(handle).addClass('ui-slider-handle-active');
			if(hard) this.currentHandle.parent()[0].focus();
		},
		blur: function(handle) {
			$(handle).removeClass('ui-slider-handle-active');
			if(this.currentHandle && this.currentHandle[0] == handle) { this.previousHandle = this.currentHandle; this.currentHandle = null; };
		},
		value: function(handle) {
			if(this.handle.length == 1) this.currentHandle = this.handle;
			var value = ((parseInt($(handle != undefined ? this.handle[handle] || handle : this.currentHandle).css(this.properties[0]),10) / (this.size - this.handleSize())) * this.options.realMaxValue) + this.options.minValue;
			var o = this.options;
			if (o.stepping) {
			    value = Math.round(value / o.stepping) * o.stepping;
			}
			return value;
		},
		convertValue: function(value) {
			return this.options.minValue + (value / (this.size - this.handleSize())) * this.options.realMaxValue;
		},
		translateValue: function(value) {
			return ((value - this.options.minValue) / this.options.realMaxValue) * (this.size - this.handleSize());
		},
		handleSize: function(handle) {
			return $(handle != undefined ? this.handle[handle] : this.currentHandle)['outer'+this.properties[1].substr(0,1).toUpperCase()+this.properties[1].substr(1)]();	
		},
		click: function(e) {
		
			// This method is only used if:
			// - The user didn't click a handle
			// - The Slider is not disabled
			// - There is a current, or previous selected handle (otherwise we wouldn't know which one to move)
			var pointer = [e.pageX,e.pageY];
			var clickedHandle = false; this.handle.each(function() { if(this == e.target) clickedHandle = true;  });
			if(clickedHandle || this.disabled || !(this.currentHandle || this.previousHandle)) return;

			//If a previous handle was focussed, focus it again
			if(this.previousHandle) this.focus(this.previousHandle, 1);
			
			//Move focussed handle to the clicked position
			this.offset = this.element.offset();
			this.moveTo(this.convertValue(e[this.properties[0] == 'top' ? 'pageY' : 'pageX'] - this.offset[this.properties[0]] - this.handleSize()/2));
		},
		start: function(e, handle) {
			
			var o = this.options;
			
			this.offset = this.element.offset();
			this.handleOffset = this.currentHandle.offset();
			this.clickOffset = { top: e.pageY - this.handleOffset.top, left: e.pageX - this.handleOffset.left };
			this.firstValue = this.value();
			
			this.propagate('start', e);
			return false;
						
		},
		stop: function(e) {
			this.propagate('stop', e);
			if (this.firstValue != this.value())
				this.propagate('change', e);
			return false;
		},
		
		oneStep: function() {
			return this.options.stepping ? this.options.stepping : (this.options.realMaxValue / this.size) * 5;
		},
		
		translateRange: function(value) {
			if (this.rangeElement) {
				if (this.currentHandle[0] == this.handle[0] && value >= this.translateValue(this.value(1)))
					value = this.translateValue(this.value(1) - this.oneStep());
				if (this.currentHandle[0] == this.handle[1] && value <= this.translateValue(this.value(0)))
					value = this.translateValue(this.value(0) + this.oneStep());
			}
			if (this.options.handles) {
				var handle = this.options.handles[this.handleIndex()];
				if (value < this.translateValue(handle.min)) {
					value = this.translateValue(handle.min);
				} else if (value > this.translateValue(handle.max)) {
					value = this.translateValue(handle.max);
				}
			}
			return value;
		},
		
		handleIndex: function() {
			return this.handle.index(this.currentHandle[0])
		},
		
		translateLimits: function(value) {
			if (value >= this.size - this.handleSize())
				value = this.size - this.handleSize();
			if (value <= 0)
				value = 0;
			return value;
		},
		
		drag: function(e, handle) {
			var o = this.options;
			var position = { top: e.pageY - this.offset.top - this.clickOffset.top, left: e.pageX - this.offset.left - this.clickOffset.left};

			var modifier = position[this.properties[0]];
			
			modifier = this.translateLimits(modifier);
			
			if (o.stepping) {
				var value = this.convertValue(modifier);
				value = Math.round(value / o.stepping) * o.stepping;
				modifier = this.translateValue(value);	
			}
			
			modifier = this.translateRange(modifier);
			
			this.currentHandle.css(this.properties[0], modifier);
			if (this.rangeElement)
				this.updateRange();
			this.propagate('slide', e);
			return false;
		},
		
		moveTo: function(value, handle, noPropagation) {
			var o = this.options;
			if (handle == undefined && !this.currentHandle && this.handle.length != 1)
				return false; //If no handle has been passed, no current handle is available and we have multiple handles, return false
			if (handle == undefined && !this.currentHandle)
				handle = 0; //If only one handle is available, use it
			if (handle != undefined)
				this.currentHandle = this.previousHandle = $(this.handle[handle] || handle);
	
			if(value.constructor == String) {
				if (/^\-\=/.test(value) ) {
					value = this.value() - parseInt(value.replace('-=', ''), 10);
				} else if (/^\+\=/.test(value) ) {
					value = this.value() + parseInt(value.replace('+=', ''), 10);
				}
			}
			
			if(o.stepping)
				value = Math.round(value / o.stepping) * o.stepping;
			value = this.translateValue(value);
			value = this.translateLimits(value);
			value = this.translateRange(value);
			
			this.currentHandle.css(this.properties[0], value);
			if (this.rangeElement)
				this.updateRange();
			
			if (!noPropagation) {
				this.propagate('start', null);
				this.propagate('stop', null);
				this.propagate('change', null);
				this.propagate("slide", null);
			}
		}
	});
	
	$.ui.slider.defaults = {
		handle: ".ui-slider-handle"
	};

})(jQuery);
