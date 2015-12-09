angular.module("PYPI").controller("navigationCtrl", function ($rootScope, $scope, $location) {
	$scope.navigation = [
		{name: 'Packages', href: "/"},
		{name: 'Admin', href: "/admin"}
	];

	$scope.isActive = function (item) {
		return $location.path() == item.href;
	}
});