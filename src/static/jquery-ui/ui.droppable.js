(function($) {

	$.fn.extend({
		droppable: function(options) {
			var args = Array.prototype.slice.call(arguments, 1);
			
			return this.each(function() {
				if (typeof options == "string") {
					var drop = $.data(this, "droppable");
					if(drop) drop[options].apply(drop, args);

				} else if(!$.data(this, "droppable"))
					new $.ui.droppable(this, options);
			});
		}
	});

	
	$.ui.droppable = function(element, options) {

		//Initialize needed constants			
		this.element = $(element);
		$.data(element, "droppable", this);
		this.element.addClass("ui-droppable");		
		
		//Prepare the passed options
		this.options = $.extend({}, options);
		var o = this.options; var accept = o.accept;
		$.extend(o, {
			accept: o.accept && o.accept.constructor == Function ? o.accept : function(d) {
				return $(d).is(accept);	
			},
			tolerance: o.tolerance || 'intersect'		
		});
		
		$(element).bind("setData.draggable", function(event, key, value){
			o[key] = value;
		}).bind("getData.draggable", function(event, key){
			return o[key];
		});
		
		//Store the droppable's proportions
		this.proportions = { width: this.element.outerWidth(), height: this.element.outerHeight() };
		
		// Add the reference and positions to the manager
		$.ui.ddmanager.droppables.push({ item: this, over: 0, out: 1 });
			
	};
	
	$.extend($.ui.droppable.prototype, {
		plugins: {},
		ui: function(c) {
			return {
				instance: this,
				draggable: (c.currentItem || c.element),
				helper: c.helper,
				position: c.position,
				absolutePosition: c.positionAbs,
				options: this.options,
				element: this.element	
			};		
		},
		destroy: function() {
			var drop = $.ui.ddmanager.droppables;
			for ( var i = 0; i < drop.length; i++ )
				if ( drop[i].item == this )
					drop.splice(i, 1);
			
			this.element
				.removeClass("ui-droppable ui-droppable-disabled")
				.removeData("droppable")
				.unbind(".droppable");
		},
		enable: function() {
			this.element.removeClass("ui-droppable-disabled");
			this.disabled = false;
		},
		disable: function() {
			this.element.addClass("ui-droppable-disabled");
			this.disabled = true;
		},
		over: function(e) {

			var draggable = $.ui.ddmanager.current;
			if (!draggable || (draggable.currentItem || draggable.element)[0] == this.element[0]) return; // Bail if draggable and droppable are same element
			
			if (this.options.accept.call(this.element,(draggable.currentItem || draggable.element))) {
				$.ui.plugin.call(this, 'over', [e, this.ui(draggable)]);
				this.element.triggerHandler("dropover", [e, this.ui(draggable)], this.options.over);
			}
			
		},
		out: function(e) {

			var draggable = $.ui.ddmanager.current;
			if (!draggable || (draggable.currentItem || draggable.element)[0] == this.element[0]) return; // Bail if draggable and droppable are same element

			if (this.options.accept.call(this.element,(draggable.currentItem || draggable.element))) {
				$.ui.plugin.call(this, 'out', [e, this.ui(draggable)]);
				this.element.triggerHandler("dropout", [e, this.ui(draggable)], this.options.out);
			}
			
		},
		drop: function(e,custom) {

			var draggable = custom || $.ui.ddmanager.current;
			if (!draggable || (draggable.currentItem || draggable.element)[0] == this.element[0]) return; // Bail if draggable and droppable are same element
			
			var childrenIntersection = false;
			this.element.children(".ui-droppable").each(function() {
				var inst = $.data(this, 'droppable');
				if(inst.options.greedy && $.ui.intersect(draggable, { item: inst, offset: inst.element.offset() }, inst.options.tolerance)) childrenIntersection = true;
			});
			if(childrenIntersection) return;
			
			if(this.options.accept.call(this.element,(draggable.currentItem || draggable.element))) {
				$.ui.plugin.call(this, 'drop', [e, this.ui(draggable)]);
				this.element.triggerHandler("drop", [e, this.ui(draggable)], this.options.drop);
			}
			
		},
		activate: function(e) {

			var draggable = $.ui.ddmanager.current;
			$.ui.plugin.call(this, 'activate', [e, this.ui(draggable)]);
			if(draggable) this.element.triggerHandler("dropactivate", [e, this.ui(draggable)], this.options.activate);
				
		},
		deactivate: function(e) {
			
			var draggable = $.ui.ddmanager.current;
			$.ui.plugin.call(this, 'deactivate', [e, this.ui(draggable)]);
			if(draggable) this.element.triggerHandler("dropdeactivate", [e, this.ui(draggable)], this.options.deactivate);
			
		}
	});
	
	$.ui.intersect = function(draggable, droppable, toleranceMode) {

		if (!droppable.offset) return false;

		var x1 = draggable.positionAbs.left, x2 = x1 + draggable.helperProportions.width,
		    y1 = draggable.positionAbs.top, y2 = y1 + draggable.helperProportions.height;
		var l = droppable.offset.left, r = l + droppable.item.proportions.width, 
		    t = droppable.offset.top,  b = t + droppable.item.proportions.height;

		switch (toleranceMode) {
			case 'fit':
				return (   l < x1 && x2 < r
					&& t < y1 && y2 < b);
				break;
			case 'intersect':
				return (   l < x1 + (draggable.helperProportions.width  / 2)        // Right Half
					&&     x2 - (draggable.helperProportions.width  / 2) < r    // Left Half
					&& t < y1 + (draggable.helperProportions.height / 2)        // Bottom Half
					&&     y2 - (draggable.helperProportions.height / 2) < b ); // Top Half
				break;
			case 'pointer':
				return (   l < (draggable.positionAbs.left + draggable.clickOffset.left) && (draggable.positionAbs.left + draggable.clickOffset.left) < r
					&& t < (draggable.positionAbs.top + draggable.clickOffset.top) && (draggable.positionAbs.top + draggable.clickOffset.top) < b);
				break;
			case 'touch':
				return (   (l < x1 && x1 < r && t < y1 && y1 < b)    // Top-Left Corner
					|| (l < x1 && x1 < r && t < y2 && y2 < b)    // Bottom-Left Corner
					|| (l < x2 && x2 < r && t < y1 && y1 < b)    // Top-Right Corner
					|| (l < x2 && x2 < r && t < y2 && y2 < b) ); // Bottom-Right Corner
				break;
			default:
				return false;
				break;
			}
		
	};
	
	/*
		This manager tracks offsets of draggables and droppables
	*/
	$.ui.ddmanager = {
		current: null,
		droppables: [],
		prepareOffsets: function(t, e) {

			var m = $.ui.ddmanager.droppables;
			var type = e ? e.type : null; // workaround for #2317
			for (var i = 0; i < m.length; i++) {
				
				if(m[i].item.disabled || (t && !m[i].item.options.accept.call(m[i].item.element,(t.currentItem || t.element)))) continue;
				m[i].offset = $(m[i].item.element).offset();
				m[i].item.proportions = { width: m[i].item.element.outerWidth(), height: m[i].item.element.outerHeight() };
				
				if(type == "dragstart") m[i].item.activate.call(m[i].item, e); //Activate the droppable if used directly from draggables
			}
			
		},
		drop: function(draggable, e) {
			
			$.each($.ui.ddmanager.droppables, function() {
				
				if (!this.item.disabled && $.ui.intersect(draggable, this, this.item.options.tolerance))
					this.item.drop.call(this.item, e);
					
				if (!this.item.disabled && this.item.options.accept.call(this.item.element,(draggable.currentItem || draggable.element))) {
					this.out = 1; this.over = 0;
					this.item.deactivate.call(this.item, e);
				}
				
			});
			
		},
		drag: function(draggable, e) {
			
			//If you have a highly dynamic page, you might try this option. It renders positions every time you move the mouse.
			if(draggable.options.refreshPositions) $.ui.ddmanager.prepareOffsets(draggable, e);
		
			//Run through all droppables and check their positions based on specific tolerance options
			$.each($.ui.ddmanager.droppables, function() {

				if(this.item.disabled) return; 
				var intersects = $.ui.intersect(draggable, this, this.item.options.tolerance);

				var c = !intersects && this.over == 1 ? 'out' : (intersects && this.over == 0 ? 'over' : null);
				if(!c) return;
					
				this[c] = 1; this[c == 'out' ? 'over' : 'out'] = 0;
				this.item[c].call(this.item, e);
					
			});
			
		}
	};
	
})(jQuery);

