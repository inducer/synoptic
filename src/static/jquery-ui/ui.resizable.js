(function($) {
	
	$.fn.resizable = function(options) {
		return this.each(function() {
			var args = Array.prototype.slice.call(arguments, 1);
			
			if (typeof options == "string") {
				var resize = $.data(this, "resizable");
				if (resize) resize[options].apply(resize, args);

			} else if(!$(this).is(".ui-resizable"))
				new $.ui.resizable(this, options);
				
		});
	};
	
	$.ui.resizable = function(element, options) {
		//Initialize needed constants
		var self = this;
		
		this.element = $(element);
		
		$.data(element, "resizable", this);
		
		// simulate .ui-resizable { position: relative; }
		var elpos = this.element.css('position');
		this.element.addClass("ui-resizable").css({ position: /static/.test(elpos) ? 'relative' : elpos });
		
		//Prepare the passed options
		this.options = $.extend({
			preventDefault: true,
			transparent: false,
			minWidth: 10,
			minHeight: 10,
			aspectRatio: false,
			disableSelection: true,
			preserveCursor: true,
			autohide: false,
			knobHandles: false
		}, options);
		
		this.options._aspectRatio = !!(this.options.aspectRatio);
		
		// force proxy if helper is enabled
		this.options.proxy = this.options.proxy || this.options.ghost ? 'proxy' : null; 
		
		// force proxy if animation is enabled
		this.options.proxy = this.options.proxy || this.options.animate ? 'proxy' : null; 
		
		// if knobHandles equals true set to ui-resizable-knob-handle
		this.options.knobHandles = this.options.knobHandles === true ? 'ui-resizable-knob-handle' : this.options.knobHandles;
		
		$(element).bind("setData.resizable", function(event, key, value){
			self.options[key] = value;
		}).bind("getData.resizable", function(event, key){
			return self.options[key];
		});
	
		var o = this.options;
	
		//Default Theme
		var aBorder = '1px solid #DEDEDE';
	
		o.defaultTheme = {
			'ui-resizable': { display: 'block' },
			'ui-resizable-handle': { position: 'absolute', background: '#F2F2F2', fontSize: '0.1px' },
			'ui-resizable-n': { cursor: 'n-resize', height: '4px', left: '0px', right: '0px', borderTop: aBorder },
			'ui-resizable-s': { cursor: 's-resize', height: '4px', left: '0px', right: '0px', borderBottom: aBorder },
			'ui-resizable-e': { cursor: 'e-resize', width: '4px', top: '0px', bottom: '0px', borderRight: aBorder },
			'ui-resizable-w': { cursor: 'w-resize', width: '4px', top: '0px', bottom: '0px', borderLeft: aBorder },
			'ui-resizable-se': { cursor: 'se-resize', width: '4px', height: '4px', borderRight: aBorder, borderBottom: aBorder },
			'ui-resizable-sw': { cursor: 'sw-resize', width: '4px', height: '4px', borderBottom: aBorder, borderLeft: aBorder },
			'ui-resizable-ne': { cursor: 'ne-resize', width: '4px', height: '4px', borderRight: aBorder, borderTop: aBorder },
			'ui-resizable-nw': { cursor: 'nw-resize', width: '4px', height: '4px', borderLeft: aBorder, borderTop: aBorder }
		};
		
		o.knobTheme = {
			'ui-resizable-handle': { background: '#F2F2F2', border: '1px solid #808080', height: '7px', width: '7px' },
			'ui-resizable-n': { cursor: 'n-resize', top: '-4px', left: '45%' },
			'ui-resizable-s': { cursor: 's-resize', bottom: '-4px', left: '45%' },
			'ui-resizable-e': { cursor: 'e-resize', right: '-4px', top: '45%' },
			'ui-resizable-w': { cursor: 'w-resize', left: '-4px', top: '45%' },
			'ui-resizable-se': { cursor: 'se-resize', right: '-4px', bottom: '-4px' },
			'ui-resizable-sw': { cursor: 'sw-resize', left: '-4px', bottom: '-4px' },
			'ui-resizable-nw': { cursor: 'nw-resize', left: '-4px', top: '-4px' },
			'ui-resizable-ne': { cursor: 'ne-resize', right: '-4px', top: '-4px' }
		};
	
		//Position the node
		if(!o.proxy && (this.element.css('position') == 'static' || this.element.css('position') == ''))
			this.element.css('position', 'relative');
	
		o._nodeName = element.nodeName;
	
		//Wrap the element if it cannot hold child nodes
		if(o._nodeName.match(/textarea|input|select|button|img/i)) {
	
			//Create a wrapper element and set the wrapper to the new current internal element
			this.element.wrap('<div class="ui-wrapper"	style="overflow: hidden; position: relative; width: '+this.element.outerWidth()+'px; height: '+this.element.outerHeight()+';"></div>');
			var oel = this.element; element = element.parentNode; this.element = $(element);
	
			//Move margins to the wrapper
			this.element.css({ marginLeft: oel.css("marginLeft"), marginTop: oel.css("marginTop"),
				marginRight: oel.css("marginRight"), marginBottom: oel.css("marginBottom")
			});
	
			oel.css({ marginLeft: 0, marginTop: 0, marginRight: 0, marginBottom: 0});
	
			//Prevent Safari textarea resize
			if ($.browser.safari && o.preventDefault) oel.css('resize', 'none');
	
			o.proportionallyResize = oel.css({ /*position: 'static',*/ zoom: 1, display: 'block' });
			
			// avoid IE jump
			this.element.css({ margin: oel.css('margin') });
			
			// fix handlers offset
			this._proportionallyResize();
		}
	
		if(!o.handles) o.handles = !$('.ui-resizable-handle', element).length ? "e,s,se" : { n: '.ui-resizable-n', e: '.ui-resizable-e', s: '.ui-resizable-s', w: '.ui-resizable-w', se: '.ui-resizable-se', sw: '.ui-resizable-sw', ne: '.ui-resizable-ne', nw: '.ui-resizable-nw' };
		if(o.handles.constructor == String) {
	
			if(o.handles == 'all')
				o.handles = 'n,e,s,w,se,sw,ne,nw';
	
			var n = o.handles.split(","); o.handles = {};
	
			o.zIndex = o.zIndex || 1000;
			
			// insertions are applied when don't have theme loaded
			var insertionsDefault = {
				handle: 'position: absolute; display: none; overflow:hidden;',
				n: 'top: 0pt; width:100%;',
				e: 'right: 0pt; height:100%;',
				s: 'bottom: 0pt; width:100%;',
				w: 'left: 0pt; height:100%;',
				se: 'bottom: 0pt; right: 0px;',
				sw: 'bottom: 0pt; left: 0px;',
				ne: 'top: 0pt; right: 0px;',
				nw: 'top: 0pt; left: 0px;'
			};
	
			for(var i = 0; i < n.length; i++) {
				var handle = jQuery.trim(n[i]), dt = o.defaultTheme, hname = 'ui-resizable-'+handle, loadDefault = !$.ui.css(hname) && !o.knobHandles, userKnobClass = $.ui.css('ui-resizable-knob-handle'), 
							allDefTheme = $.extend(dt[hname], dt['ui-resizable-handle']), allKnobTheme = $.extend(o.knobTheme[hname], !userKnobClass ? o.knobTheme['ui-resizable-handle'] : {});
				
				// increase zIndex of sw, se, ne, nw axis
				var applyZIndex = /sw|se|ne|nw/.test(handle) ? { zIndex: ++o.zIndex } : {};
				
				var defCss = (loadDefault ? insertionsDefault[handle] : ''), 
					axis = $(['<div class="ui-resizable-handle ', hname, '" style="', defCss, insertionsDefault.handle, '"></div>'].join('')).css( applyZIndex );
				o.handles[handle] = '.ui-resizable-'+handle;
				
				this.element.append(
					//Theme detection, if not loaded, load o.defaultTheme
					axis.css( loadDefault ? allDefTheme : {} )
						// Load the knobHandle css, fix width, height, top, left...
						.css( o.knobHandles ? allKnobTheme : {} ).addClass('ui-resizable-knob-handle').addClass(o.knobHandles)
				);
			}
			
			if (o.knobHandles) this.element.addClass('ui-resizable-knob').css( !$.ui.css('ui-resizable-knob') ? { /*border: '1px #fff dashed'*/ } : {} );
		}
	
		this._renderAxis = function(target) {
			target = target || this.element;
	
			for(var i in o.handles) {
				if(o.handles[i].constructor == String) 
					o.handles[i] = $(o.handles[i], element).show();
	
				if (o.transparent)
					o.handles[i].css({opacity:0});
	
				//Apply pad to wrapper element, needed to fix axis position (textarea, inputs, scrolls)
				if (this.element.is('.ui-wrapper') && 
					o._nodeName.match(/textarea|input|select|button/i)) {
	
					var axis = $(o.handles[i], element), padWrapper = 0;
	
					//Checking the correct pad and border
					padWrapper = /sw|ne|nw|se|n|s/.test(i) ? axis.outerHeight() : axis.outerWidth();
	
					//The padding type i have to apply...
					var padPos = [ 'padding', 
						/ne|nw|n/.test(i) ? 'Top' :
						/se|sw|s/.test(i) ? 'Bottom' : 
						/^e$/.test(i) ? 'Right' : 'Left' ].join(""); 
	
					if (!o.transparent)
						target.css(padPos, padWrapper);
	
					this._proportionallyResize();
				}
				if(!$(o.handles[i]).length) continue;
			}
		};
			
		this._renderAxis(this.element);
		o._handles = $('.ui-resizable-handle', self.element);
		
		if (o.disableSelection)
			o._handles.each(function(i, e) { $.ui.disableSelection(e); });
		
		//Matching axis name
		o._handles.mouseover(function() {
			if (!o.resizing) {
				if (this.className) 
					var axis = this.className.match(/ui-resizable-(se|sw|ne|nw|n|e|s|w)/i);
				//Axis, default = se
				o.axis = axis && axis[1] ? axis[1] : 'se';
			}
		});
				
		//If we want to auto hide the elements
		if (o.autohide) {
			o._handles.hide();
			$(self.element).addClass("ui-resizable-autohide").hover(function() {
				$(this).removeClass("ui-resizable-autohide");
				o._handles.show();
			},
			function(){
				if (!o.resizing) {
					$(this).addClass("ui-resizable-autohide");
					o._handles.hide();
				}
			});
		}
	
		//Initialize mouse events for interaction
		this.element.mouseInteraction({
			executor: this,
			delay: 0,
			distance: 0,
			dragPrevention: ['input','textarea','button','select','option'],
			start: this.start,
			stop: this.stop,
			drag: this.drag,
			condition: function(e) {
				if(this.disabled) return false;
				for(var i in this.options.handles) {
					if($(this.options.handles[i])[0] == e.target) return true;
				}
				return false;
			}
		});
	};

	$.extend($.ui.resizable.prototype, {
		plugins: {},
		ui: function() {
			return {
				instance: this,
				axis: this.options.axis,
				options: this.options
			};
		},
		_renderProxy: function() {
			var el = this.element, o = this.options;
			this.elementOffset = el.offset();
	
			if(o.proxy) {
				this.helper = this.helper || $('<div style="overflow:hidden;"></div>');
	
				// fix ie6 offset
				var ie6 = $.browser.msie && $.browser.version  < 7, ie6offset = (ie6 ? 1 : 0),
				pxyoffset = ( ie6 ? 2 : -1 );
	
				this.helper.addClass(o.proxy).css({
					width: el.outerWidth() + pxyoffset,
					height: el.outerHeight() + pxyoffset,
					position: 'absolute',
					left: this.elementOffset.left - ie6offset +'px',
					top: this.elementOffset.top - ie6offset +'px',
					zIndex: ++o.zIndex
				});
				
				this.helper.appendTo("body");
	
				if (o.disableSelection)
					$.ui.disableSelection(this.helper.get(0));
	
			} else {
				this.helper = el; 
			}
		},
		propagate: function(n,e) {
			$.ui.plugin.call(this, n, [e, this.ui()]);
			this.element.triggerHandler(n == "resize" ? n : ["resize", n].join(""), [e, this.ui()], this.options[n]);
		},
		destroy: function() {
			this.element
			.removeClass("ui-resizable ui-resizable-disabled")
			.removeMouseInteraction()
			.removeData("resizable")
			.unbind(".resizable").find('.ui-resizable-handle').remove();
		},
		enable: function() {
			this.element.removeClass("ui-resizable-disabled");
			this.disabled = false;
		},
		disable: function() {
			this.element.addClass("ui-resizable-disabled");
			this.disabled = true;
		},
		start: function(e) {
			var o = this.options, iniPos = this.element.position(), el = this.element;
			o.resizing = true;
			o.documentScroll = { top: $(document).scrollTop(), left: $(document).scrollLeft() };
	
			// buf fix #1749
			if (el.is('.ui-draggable') || (/absolute/).test(el.css('position'))) {
				// sOffset decides if document scrollOffset will be added to the top/left of the resizable element
				var sOffset = $.browser.msie && !o.containment && (/absolute/).test(el.css('position')) && !(/relative/).test(el.parent().css('position'));
				var dscrollt = sOffset ? o.documentScroll.top : 0, dscrolll = sOffset ? o.documentScroll.left : 0;
				el.css({ position: 'absolute', top: (iniPos.top + dscrollt), left: (iniPos.left + dscrolll) });
			}
	
			//Opera fixing relative position
			if (/relative/.test(el.css('position')) && $.browser.opera)
			el.css({ position: 'relative', top: 'auto', left: 'auto' });
	
			this._renderProxy();
	
			var curleft = parseInt(this.helper.css('left'),10) || 0, curtop = parseInt(this.helper.css('top'),10) || 0;
			
			//Store needed variables
			this.offset = this.helper.offset();
			this.position = { left: curleft, top: curtop };
			this.size = o.proxy ? { width: el.outerWidth(), height: el.outerHeight() } : { width: el.width(), height: el.height() };
			this.originalSize = o.proxy ? { width: el.outerWidth(), height: el.outerHeight() } : { width: el.width(), height: el.height() };
			this.originalPosition = { left: curleft, top: curtop };
			this.sizeDiff = { width: el.outerWidth() - el.width(), height: el.outerHeight() - el.height() };
			this.originalMousePosition = { left: e.pageX, top: e.pageY };
			
			//Aspect Ratio
			o.aspectRatio = (typeof o.aspectRatio == 'number') ? o.aspectRatio : ((this.originalSize.height / this.originalSize.width)||1);
	
			if (o.preserveCursor)
				$('body').css('cursor', o.axis + '-resize');
				
			this.propagate("start", e); 	
			return false;
		},
		stop: function(e) {
			this.options.resizing = false;
			var o = this.options;
	
			if(o.proxy) {
				var pr = o.proportionallyResize, ista = pr && /textarea/i.test(pr.get(0).nodeName), 
							soffseth = ista && $.ui.hasScroll(pr.get(0), 'left') /* TODO - jump height */ ? 0 : this.sizeDiff.height,
							soffsetw = ista ? 0 : this.sizeDiff.width;
				
				var style = {
					width: (this.helper.width() - soffsetw) + "px",
					height: (this.helper.height() - soffseth) + "px",
					top: ((parseInt(this.element.css('top'),10) || 0) + ((parseInt(this.helper.css('top'),10) - this.elementOffset.top)||0)),
					left: ((parseInt(this.element.css('left'),10) || 0) + ((parseInt(this.helper.css('left'),10) - this.elementOffset.left)||0))
				};
				
				if (!o.animate)
					this.element.css(style);
				
				if (o.proxy && !o.animate) this._proportionallyResize();
				this.helper.remove();
			}

			if (o.preserveCursor)
			$('body').css('cursor', 'auto');
	
			this.propagate("stop", e);	
			return false;
		},
		drag: function(e) {
			//Increase performance, avoid regex
			var el = this.helper, o = this.options, props = {},
				self = this, smp = this.originalMousePosition, a = o.axis;

			var dx = (e.pageX-smp.left)||0, dy = (e.pageY-smp.top)||0;
			var trigger = this.change[a];
			if (!trigger) return false;
		 
			// Calculate the attrs that will be change
			var data = trigger.apply(this, [e, dx, dy]), ie6 = $.browser.msie && $.browser.version < 7, csdif = this.sizeDiff;
		 
			// Adjust currentSizeDiff on resize
			if (data.width) data.width = data.width + (!o.proxy && ie6 ? csdif.width : 0);
			if (data.height) data.height = data.height + (!o.proxy && ie6 ? csdif.height : 0);
		 
			if (o._aspectRatio || e.shiftKey)
				data = this._updateRatio(data, e);
			
			data = this._respectSize(data, e);
			
			this.propagate("resize", e);
			
			el.css({
				top: this.position.top + "px", left: this.position.left + "px", 
				width: this.size.width + "px", height: this.size.height + "px"
			});
			
			if (!o.proxy && o.proportionallyResize)
				this._proportionallyResize();
			
			this._updateCache(data);
			
			return false;
		},
		
		_updateCache: function(data) {
			var o = this.options;
			this.offset = this.helper.offset();
			if (data.left) this.position.left = data.left;
			if (data.top) this.position.top = data.top;
			if (data.height) this.size.height = data.height;
			if (data.width) this.size.width = data.width;
		},
		
		_updateRatio: function(data, e) {
			var o = this.options, cpos = this.position, csize = this.size, a = o.axis;
			
			if (data.height) data.width = csize.height / o.aspectRatio;
			else if (data.width) data.height = csize.width * o.aspectRatio;
			
			if (a == 'sw') {
				data.left = cpos.left + (csize.width - data.width);
				data.top = null;
			}
			if (a == 'nw') { 
				data.top = cpos.top + (csize.height - data.height);
				data.left = cpos.left + (csize.width - data.width);
			}
			
			return data;
		},
		
		_respectSize: function(data, e) {
			
			var el = this.helper, o = this.options, pRatio = o._aspectRatio || e.shiftKey,  a = o.axis, 
					ismaxw = data.width && o.maxWidth && o.maxWidth < data.width, ismaxh = data.height && o.maxHeight && o.maxHeight < data.height,
						isminw = data.width && o.minWidth && o.minWidth > data.width, isminh = data.height && o.minHeight && o.minHeight > data.height;
			
			if (isminw) data.width = o.minWidth;
			if (isminh) data.height = o.minHeight;
			if (ismaxw) data.width = o.maxWidth;
			if (ismaxh) data.height = o.maxHeight;
			
			var dw = this.originalPosition.left + this.originalSize.width, dh = this.position.top + this.size.height;
			var cw = /sw|nw|w/.test(a), ch = /nw|ne|n/.test(a);
			
			if (isminw && cw) data.left = dw - o.minWidth;
			if (ismaxw && cw) data.left = dw - o.maxWidth;
			if (isminh && ch)	data.top = dh - o.minHeight;
			if (ismaxh && ch)	data.top = dh - o.maxHeight;
			
			// fixing jump error on top/left - bug #2330
			var isNotwh = !data.width && !data.height;
			if (isNotwh && !data.left && data.top) data.top = null;
			else if (isNotwh && !data.top && data.left) data.left = null;
			
			return data;
		},
		
		_proportionallyResize: function() {
			var o = this.options;
			if (!o.proportionallyResize) return;
			var prel = o.proportionallyResize, el = this.helper || this.element;
		 
			if (!o.borderDif) {
				var b = [prel.css('borderTopWidth'), prel.css('borderRightWidth'), prel.css('borderBottomWidth'), prel.css('borderLeftWidth')],
					p = [prel.css('paddingTop'), prel.css('paddingRight'), prel.css('paddingBottom'), prel.css('paddingLeft')];
				 
				o.borderDif = $.map(b, function(v, i) {
					var border = parseInt(v,10)||0, padding = parseInt(p[i],10)||0;
					return border + padding; 
				});
			}
			prel.css({
				height: (el.height() - o.borderDif[0] - o.borderDif[2]) + "px",
				width: (el.width() - o.borderDif[1] - o.borderDif[3]) + "px"
			});
		},
		
		change: {
			e: function(e, dx, dy) {
				return { width: this.originalSize.width + dx };
			},
			w: function(e, dx, dy) {
				var o = this.options, cs = this.originalSize, sp = this.originalPosition;
				return { left: sp.left + dx, width: cs.width - dx };
			},
			n: function(e, dx, dy) {
				var o = this.options, cs = this.originalSize, sp = this.originalPosition;
				return { top: sp.top + dy, height: cs.height - dy };
			},
			s: function(e, dx, dy) {
				return { height: this.originalSize.height + dy };
			},
			se: function(e, dx, dy) {
				return $.extend(this.change.s.apply(this, arguments), this.change.e.apply(this, [e, dx, dy]));
			},
			sw: function(e, dx, dy) {
				return $.extend(this.change.s.apply(this, arguments), this.change.w.apply(this, [e, dx, dy]));
			},
			ne: function(e, dx, dy) {
				return $.extend(this.change.n.apply(this, arguments), this.change.e.apply(this, [e, dx, dy]));
			},
			nw: function(e, dx, dy) {
				return $.extend(this.change.n.apply(this, arguments), this.change.w.apply(this, [e, dx, dy]));
			}
		}
	});

})(jQuery);
