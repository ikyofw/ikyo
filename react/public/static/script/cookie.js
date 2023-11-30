Cookie = function() {
}
Cookie.prototype = {
	add : function(name, value, days) {
		var days = 1;
		if (days) {
			var date = new Date();
			date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
			var expires = "; expires=" + date.toGMTString();
		} else {
			var expires = "";
		}
		document.cookie = name + "=" + value + expires + "; path=/";
	},
	read : function(name) {
		var nameSG = name + "=";
		var nuller = '';
		if (document.cookie.indexOf(nameSG) == -1) {
			return nuller;
		}

		var ca = document.cookie.split(';');
		for ( var i = 0; i < ca.length; i++) {
			var c = ca[i];
			while (c.charAt(0) == ' ') {
				c = c.substring(1, c.length);
			}
			if (c.indexOf(nameSG) == 0) {
				return c.substring(nameSG.length, c.length);
			}
		}
		return null;
	},
	erase : function(name) {
		this.add(name, "", 1);
	}
}
