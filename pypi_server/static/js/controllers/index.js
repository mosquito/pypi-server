angular.module("PYPI").controller("indexCtrl", function ($rootScope, $uibModal, API) {
	$rootScope.loginModal = function () {
		return $uibModal.open({
			templateUrl: 'loginTmpl',
			controller: function ($scope, $modalInstance) {
				$scope.loginData = {};

				$scope.doLogin = function () {
					API.login.authorize(
						$scope.loginData.login,
						$scope.loginData.password
					).then(function (userInfo) {
						$scope.loginData = {};
						$modalInstance.close(userInfo);
					}, function () {

					});
				};
			},
			size: 'md'
		}).result;
	};
});