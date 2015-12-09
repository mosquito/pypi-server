angular.module("PYPI").factory('API', function($http, $q, $rootScope, modals) {
	function rest(url, method, data, handleErrors, background) {
		method = method || 'get';
		data = data || null;
		background = background || false;
		handleErrors = (typeof handleErrors === 'undefined')?true:handleErrors;

		var defer = $q.defer();

		var cllee = $http[method];
		var params = [url];

		if (data) {
			params.push(data)
		}

		if (!background) {
			$rootScope.loader[url] = false;
		}

		cllee.apply(cllee, params).then(
			function (response) {
				if (!background) {
					$rootScope.loader[url] = true;
				}
				defer.resolve(response.data);
			},
			function (response) {
				if (!background) {
					$rootScope.loader[url] = true;
				}
				if (handleErrors) {
					modals.error("Error when processing " + url, response.statusText);
				}
				defer.reject(response);
			}
		);
		return defer.promise;
	}

	return {
		login: {
			check: function () {
				return rest('/api/v1/login', 'get', null, false);
			},
			authorize: function (login, password) {
				return rest('/api/v1/login', 'post', {login: login, password: password});
			}
		},
		package: {
			list: function () {
				return rest('/api/v1/packages');
			},
			info: function (name) {
				return rest('/api/v1/package/' + name + '/');
			},
			versionInfo: function (name, version) {
				return rest('/api/v1/package/' + name + '/' + version + '/');
			}
		},
		user: {
			list: function () {
				return rest('/api/v1/users/');
			},
			create: function (login, password, email, isAdmin) {
				isAdmin = isAdmin || false;

				return rest('/api/v1/users/', 'post', {
					"is_admin": isAdmin,
					"login": login,
					"password": password,
					"email": email
				});
			},
			info: function (id) {
				return rest('/api/v1/user/' + id + '/')
			},
			modify: function (id, user) {
				return rest('/api/v1/user/' + id + '/', 'put', user);
			},
			delete: function (id) {
				return rest('/api/v1/user/' + id + '/', 'delete');
			}
		}
	};
});