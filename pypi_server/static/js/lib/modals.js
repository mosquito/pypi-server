angular.module("PYPI").factory('modals', ['$uibModal', function($uibModal) {
	return {
		error: function (text, title) {
			title = title || 'Error';
			return $uibModal.open({
				templateUrl: 'errorTmpl',
				controller: function ($scope, $modalInstance, text, title) {
					$scope.text = text;
					$scope.title = title;
					$scope.cancel = function () {
						$modalInstance.dismiss('cancel');
					};
				},
				resolve: {
					text: function () {
						return text;
					},
					title: function () {
						return title;
					}
				},
				size: 'md'
			}).result;
		},
		confirm: function (text, title) {
			title = title || 'Confirm';
			return $uibModal.open({
				templateUrl: 'confirmTmpl',
				controller: function ($scope, $modalInstance, text, title) {
					$scope.text = text;
					$scope.title = title;
					$scope.ok = function () {
						$modalInstance.close(true);
					};
					$scope.cancel = function () {
						$modalInstance.dismiss(false);
					};
				},
				resolve: {
					text: function () {
						return text;
					},
					title: function () {
						return title;
					}
				},
				size: 'md'
			}).result;
		},
		alert: function (text, title) {
			title = title || 'Info';
			return $uibModal.open({
				templateUrl: 'alertTmpl',
				controller: function ($scope, $modalInstance, text, title) {
					$scope.text = text;
					$scope.title = title;
					$scope.ok = function () {
						$modalInstance.close(true);
					};
					$scope.cancel = function () {
						$modalInstance.dismiss(false);
					};
				},
				resolve: {
					text: function () {
						return text;
					},
					title: function () {
						return title;
					}
				},
				size: 'md'
			}).result;
		},
		edit: function (initial, text, title) {
			title = title || 'Edit';
			initial = initial || '';

			return $uibModal.open({
				templateUrl: 'editTmpl',
				controller: function ($scope, $modalInstance, text, title, initial) {
					$scope.text = text;
					$scope.title = title;
					$scope.value = initial;
					$scope.ok = function () {
						$modalInstance.close($scope.value);
					};
					$scope.cancel = function () {
						$modalInstance.dismiss($scope.value);
					};
				},
				resolve: {
					text: function () {
						return text;
					},
					title: function () {
						return title;
					},
					initial: function () {
						return initial;
					}
				},
				size: 'md'
			}).result;
		}
	}
}]);