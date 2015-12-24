angular.module("PYPI").controller("packagesCtrl", function ($rootScope, $scope, $interval, API, modals) {
	$scope.packages = [];

	function updatePackages() {
		API.package.list().then(function(data) {
			$scope.packages = data.map(function (pkg, $index) {
				$scope.$watch('packages[' + $index + '].open', function(value) {
					if (value) {
						updatePackage(pkg);
					}
				});
				pkg.remove = function () {
					modals.confirm('You really want to delete package "' + pkg.name + '"?').then(function () {
						API.package.remove(pkg.name).then(function () {
							modals.alert('Package "' + pkg.name + '" deleted.' , 'Package deleted');
							updatePackages();
						});
					});
				};
				pkg.changeOwner = function (owner) {
					return API.package.changeOwner(pkg.name, owner);
				};
				return pkg;
			});
		});
	}

	function onPageLoad() {
		API.login.check().then(updatePackages, function () {
			$rootScope.loginModal().then(updatePackages, onPageLoad);
		});
	}

	onPageLoad();

	function updatePackage (pkg) {
		return API.package.info(pkg.name).then(function (info) {
			pkg.info = info;
			pkg.info.versions = pkg.info.versions.map(function (version) {
				var ver = {
					name: version,
					info: null,
					getInfo: function () {
						API.package.version.info(pkg.name, version).then(function (data) {
							ver.info = data;
						});
					},
					remove: function () {
						modals.confirm(
							'You really want to delete version "' +
							version + '" of package "' + pkg.name + '"?'
						).then(function () {
							API.package.version.remove(pkg.name, version).then(function () {
								modals.alert('Version "' + version + '" of package "' + pkg.name + '" deleted.');
								updatePackage(pkg);
							});
						});
					},
					hide: function () {
						modals.confirm(
							'Do you want to hide version "' + ver.name +
							'" of package "' + pkg.name + '"?'
						).then(function () {
							API.package.version.hide(pkg.name, version).then(function () {
								modals.alert(pkg.name + " " + ver.name + " hidden.");
							});
						});
					}
				};

				return ver;
			});
		});
	}
});