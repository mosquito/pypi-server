angular.module("PYPI").controller("adminCtrl", function ($scope, $uibModal, modals, API) {
	$scope.users = [];

	function createUserModal () {
		return $uibModal.open({
			templateUrl: 'createUserTmpl',
			controller: function ($scope, $modalInstance) {
				$scope.create = function () {
					var passwdIsOk = (
						(
							(!!$scope.passwordFirst) &&	(!!$scope.passwordSecond)
						) &&
						($scope.passwordFirst == $scope.passwordSecond)
					);

					$scope.form.passwordFirst.$setValidity('admin', passwdIsOk);
					$scope.form.passwordSecond.$setValidity('admin', passwdIsOk);
					$scope.form.login.$setValidity('admin', (!!$scope.login));
					$scope.form.email.$setValidity('admin', (!!$scope.email));

					if ($scope.form.$valid) {
						$modalInstance.close({
							login: $scope.login,
							email: $scope.email,
							password: $scope.passwordFirst,
							isAdmin: $scope.isAdmin
						});
					}
				};
				$scope.cancel = function () {
					$modalInstance.dismiss(false);
				};
			},
			resolve: {
			},
			size: 'md'
		}).result;
	}

	function updateUserList () {
		API.user.list().then(function (users) {
			$scope.users = users;
		});
	}

	updateUserList();

	$scope.createUser = function () {
		createUserModal().then(function (userData) {
			API.user.create(
				userData.login,
				userData.password,
				userData.email,
				userData.isAdmin
			).then(function () {
				updateUserList();
				modals.alert('User "' + userData.login + '" created.');
			});
		});
	};

	$scope.updateUser = function (user) {
		API.user.modify(user.id, user).then(function (result) {
			modals.alert('User "' + user.login + '" updated.');
		})
	};

	$scope.deleteUser = function (user) {
		modals.confirm('Are you really want to delete user "' + user.login + '"?').then(function () {
			API.user.delete(user.id).then(function () {
				modals.alert('User "' + user.login + '" disabled.');
			});
		});
	};

});