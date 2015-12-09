angular.module("PYPI").controller("packagesCtrl", function ($rootScope, $scope, $interval, API) {
	$scope.packages = [];

	function updateLackages() {
		API.package.list().then(function(data) {
			$scope.packages = data;
		});
	}

	function onPageLoad() {
		API.login.check().then(updateLackages, function () {
			$rootScope.loginModal().then(updateLackages, onPageLoad);
		});
	}

	onPageLoad();

	$scope.pkgInfo = function (pkg) {
		if ('info' in pkg) {
			pkg.info = false;
		} else {
			API.package.info(pkg.name).then(function (info) {
				pkg.info = info;
			});
		}
	};
});