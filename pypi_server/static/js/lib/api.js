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
					modals.error("Error when processing " + url, response.data.error.message);
				}
				defer.reject(response);
			}
		);

		return defer.promise;
	}

	return {
		hostname: function () {
			return rest('/api/host/name', 'get');
		},
		hostInfo: function () {
			return rest('/api/host/info', 'get', null, false, true);
		},
		containers: function () {
			return rest('/api/container', 'get', null, false, true);
		},
		containerInfo: function (name) {
			return rest('/api/container/' + name, 'get');
		},
		containerSetInfo: function (name, config) {
			return rest('/api/container/' + name, 'put', {'config': config});
		},
		containerAction: function (name, action) {
			return rest('/api/container/' + name, 'post', {action: action});
		},
		asyncTasks: function () {
			return rest('/api/tasks/', 'get');
		}
	};
});