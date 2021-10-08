import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor

import dice_ml
from dice_ml.utils.exception import UserConfigValidationException
from dice_ml.explainer_interfaces.explainer_base import ExplainerBase


@pytest.mark.parametrize("method", ['random', 'genetic', 'kdtree'])
class TestExplainerBaseBinaryClassification:

    def _verify_feature_importance(self, feature_importance):
        if feature_importance is not None:
            for key in feature_importance:
                assert feature_importance[key] >= 0.0 and feature_importance[key] <= 1.0

    @pytest.mark.parametrize("desired_class", [1])
    def test_zero_totalcfs(
        self, desired_class, method, sample_custom_query_1,
        custom_public_data_interface,
        sklearn_binary_classification_model_interface
    ):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)

        with pytest.raises(UserConfigValidationException):
            exp.generate_counterfactuals(
                    query_instances=[sample_custom_query_1],
                    total_CFs=0,
                    desired_class=desired_class)

    @pytest.mark.parametrize("desired_class", [1])
    def test_local_feature_importance(
            self, desired_class, method,
            sample_custom_query_1, sample_counterfactual_example_dummy,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)
        sample_custom_query = pd.concat([sample_custom_query_1, sample_custom_query_1])
        cf_explanations = exp.generate_counterfactuals(
                    query_instances=sample_custom_query,
                    total_CFs=15,
                    desired_class=desired_class)

        cf_explanations.cf_examples_list[0].final_cfs_df = sample_counterfactual_example_dummy.copy()
        cf_explanations.cf_examples_list[0].final_cfs_df_sparse = sample_counterfactual_example_dummy.copy()
        cf_explanations.cf_examples_list[0].final_cfs_df.drop([0, 1, 2], inplace=True)
        cf_explanations.cf_examples_list[0].final_cfs_df_sparse.drop([0, 1, 2], inplace=True)

        cf_explanations.cf_examples_list[1].final_cfs_df = sample_counterfactual_example_dummy.copy()
        cf_explanations.cf_examples_list[1].final_cfs_df_sparse = sample_counterfactual_example_dummy.copy()
        cf_explanations.cf_examples_list[1].final_cfs_df.drop([0], inplace=True)
        cf_explanations.cf_examples_list[1].final_cfs_df_sparse.drop([0], inplace=True)

        local_importances = exp.local_feature_importance(
            query_instances=None,
            cf_examples_list=cf_explanations.cf_examples_list)

        for local_importance in local_importances.local_importance:
            self._verify_feature_importance(local_importance)

    @pytest.mark.parametrize("desired_class", [1])
    def test_global_feature_importance(
            self, desired_class, method,
            sample_custom_query_10, sample_counterfactual_example_dummy,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)

        cf_explanations = exp.generate_counterfactuals(
                    query_instances=sample_custom_query_10,
                    total_CFs=15,
                    desired_class=desired_class)

        cf_explanations.cf_examples_list[0].final_cfs_df = sample_counterfactual_example_dummy.copy()
        cf_explanations.cf_examples_list[0].final_cfs_df_sparse = sample_counterfactual_example_dummy.copy()
        cf_explanations.cf_examples_list[0].final_cfs_df.drop([0, 1, 2, 3, 4], inplace=True)
        cf_explanations.cf_examples_list[0].final_cfs_df_sparse.drop([0, 1, 2, 3, 4], inplace=True)

        for index in range(1, len(cf_explanations.cf_examples_list)):
            cf_explanations.cf_examples_list[index].final_cfs_df = sample_counterfactual_example_dummy.copy()
            cf_explanations.cf_examples_list[index].final_cfs_df_sparse = sample_counterfactual_example_dummy.copy()

        global_importance = exp.global_feature_importance(
            query_instances=None,
            cf_examples_list=cf_explanations.cf_examples_list)

        self._verify_feature_importance(global_importance.summary_importance)

    @pytest.mark.parametrize("desired_class", [1])
    def test_global_feature_importance_error_conditions_with_insufficient_query_points(
            self, desired_class, method,
            sample_custom_query_1,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)

        cf_explanations = exp.generate_counterfactuals(
                    query_instances=sample_custom_query_1,
                    total_CFs=15,
                    desired_class=desired_class)

        with pytest.raises(
            UserConfigValidationException,
            match="The number of points for which counterfactuals generated should be "
                  "greater than or equal to 10 "
                  "to compute global feature importance"):
            exp.global_feature_importance(
                query_instances=None,
                cf_examples_list=cf_explanations.cf_examples_list)

        with pytest.raises(
            UserConfigValidationException,
            match="The number of query instances should be greater than or equal to 10 "
                  "to compute global feature importance over all query points"):
            exp.global_feature_importance(
                query_instances=sample_custom_query_1,
                total_CFs=15,
                desired_class=desired_class)

    @pytest.mark.parametrize("desired_class", [1])
    def test_global_feature_importance_error_conditions_with_insufficient_cfs_per_query_point(
            self, desired_class, method,
            sample_custom_query_10,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)

        cf_explanations = exp.generate_counterfactuals(
                    query_instances=sample_custom_query_10,
                    total_CFs=1,
                    desired_class=desired_class)

        with pytest.raises(
            UserConfigValidationException,
            match="The number of counterfactuals generated per query instance should be "
                  "greater than or equal to 10 "
                  "to compute global feature importance over all query points"):
            exp.global_feature_importance(
                query_instances=None,
                cf_examples_list=cf_explanations.cf_examples_list)

        with pytest.raises(
            UserConfigValidationException,
            match="The number of counterfactuals requested per query instance should be greater "
                  "than or equal to 10 "
                  "to compute global feature importance over all query points"):
            exp.global_feature_importance(
                query_instances=sample_custom_query_10,
                total_CFs=1,
                desired_class=desired_class)

    @pytest.mark.parametrize("desired_class", [1])
    def test_local_feature_importance_error_conditions_with_insufficient_cfs_per_query_point(
            self, desired_class, method,
            sample_custom_query_1,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)

        cf_explanations = exp.generate_counterfactuals(
                    query_instances=sample_custom_query_1,
                    total_CFs=1,
                    desired_class=desired_class)

        with pytest.raises(
            UserConfigValidationException,
            match="The number of counterfactuals generated per query instance should be "
                  "greater than or equal to 10 to compute feature importance for all query points"):
            exp.local_feature_importance(
                query_instances=None,
                cf_examples_list=cf_explanations.cf_examples_list)

        with pytest.raises(
            UserConfigValidationException,
            match="The number of counterfactuals requested per "
                  "query instance should be greater than or equal to 10 "
                  "to compute feature importance for all query points"):
            exp.local_feature_importance(
                query_instances=sample_custom_query_1,
                total_CFs=1,
                desired_class=desired_class)

    # @pytest.mark.parametrize("desired_class, binary_classification_exp_object_out_of_order",
    #                          [(1, 'random'), (1, 'genetic'), (1, 'kdtree')],
    #                          indirect=['binary_classification_exp_object_out_of_order'])
    # def test_columns_out_of_order(self, desired_class, binary_classification_exp_object_out_of_order, sample_custom_query_1):
    #     exp = binary_classification_exp_object_out_of_order  # explainer object
    #     exp._generate_counterfactuals(
    #         query_instance=sample_custom_query_1,
    #         total_CFs=0,
    #         desired_class=desired_class,
    #         desired_range=None,
    #         permitted_range=None,
    #         features_to_vary='all')

    @pytest.mark.parametrize("desired_class", [1])
    def test_incorrect_features_to_vary_list(
            self, desired_class, method, sample_custom_query_1,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)
        with pytest.raises(
                UserConfigValidationException,
                match="Got features {" + "'unknown_feature'" + "} which are not present in training data"):
            exp.generate_counterfactuals(
                query_instances=sample_custom_query_1,
                total_CFs=10,
                desired_class=desired_class,
                desired_range=None,
                permitted_range=None,
                features_to_vary=['unknown_feature'])

    @pytest.mark.parametrize("desired_class", [1])
    def test_incorrect_features_permitted_range(
            self, desired_class, method, sample_custom_query_1,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)
        with pytest.raises(
                UserConfigValidationException,
                match="Got features {" + "'unknown_feature'" + "} which are not present in training data"):
            exp.generate_counterfactuals(
                query_instances=sample_custom_query_1,
                total_CFs=10,
                desired_class=desired_class,
                desired_range=None,
                permitted_range={'unknown_feature': [1, 30]},
                features_to_vary='all')

    @pytest.mark.parametrize("desired_class", [1])
    def test_incorrect_values_permitted_range(
            self, desired_class, method, sample_custom_query_1,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)
        with pytest.raises(UserConfigValidationException) as ucve:
            exp.generate_counterfactuals(
                query_instances=sample_custom_query_1,
                total_CFs=10,
                desired_class=desired_class,
                desired_range=None,
                permitted_range={'Categorical': ['d']},
                features_to_vary='all')

        assert 'The category {0} does not occur in the training data for feature {1}. Allowed categories are {2}'.format(
            'd', 'Categorical', ['a', 'b', 'c']) in str(ucve)

    # When no elements in the desired_class are present in the training data
    @pytest.mark.parametrize("desired_class", [100, 'a'])
    def test_unsupported_binary_class(
            self, desired_class, method, sample_custom_query_1,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)
        with pytest.raises(UserConfigValidationException) as ucve:
            exp.generate_counterfactuals(query_instances=sample_custom_query_1, total_CFs=3,
                                         desired_class=desired_class)
        if desired_class == 100:
            assert "Desired class not present in training data!" in str(ucve)
        else:
            assert "The target class for {0} could not be identified".format(desired_class) in str(ucve)

    # Testing if an error is thrown when the query instance has an unknown categorical variable
    @pytest.mark.parametrize("desired_class", [1])
    def test_query_instance_unknown_column(
            self, desired_class, method, sample_custom_query_5,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)
        with pytest.raises(ValueError, match='not present in training data'):
            exp.generate_counterfactuals(
                query_instances=sample_custom_query_5, total_CFs=3,
                desired_class=desired_class)

    # Testing if an error is thrown when the query instance has an unknown categorical variable
    @pytest.mark.parametrize("desired_class", [1])
    def test_query_instance_outside_bounds(
            self, desired_class, method, sample_custom_query_3,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)
        with pytest.raises(ValueError, match='has a value outside the dataset'):
            exp.generate_counterfactuals(query_instances=sample_custom_query_3, total_CFs=1,
                                         desired_class=desired_class)

    # # Testing that the counterfactuals are in the desired class
    @pytest.mark.parametrize("desired_class", [1])
    def test_desired_class(
            self, desired_class, method, sample_custom_query_2,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)
        ans = exp.generate_counterfactuals(query_instances=sample_custom_query_2,
                                           features_to_vary='all',
                                           total_CFs=2, desired_class=desired_class,
                                           permitted_range=None)
        if method != 'kdtree':
            assert all(ans.cf_examples_list[0].final_cfs_df[exp.data_interface.outcome_name].values == [desired_class] * 2)
        else:
            assert all(ans.cf_examples_list[0].final_cfs_df_sparse[exp.data_interface.outcome_name].values ==
                       [desired_class] * 2)

    @pytest.mark.parametrize("desired_class, total_CFs, permitted_range",
                             [(1, 1, {'Numerical': [10, 150]})])
    def test_permitted_range(
            self, desired_class, method, total_CFs, permitted_range, sample_custom_query_2,
            custom_public_data_interface,
            sklearn_binary_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)
        ans = exp.generate_counterfactuals(query_instances=sample_custom_query_2,
                                           permitted_range=permitted_range,
                                           total_CFs=total_CFs, desired_class=desired_class)

        for feature in permitted_range:
            if method != 'kdtree':
                assert all(
                    permitted_range[feature][0] <= ans.cf_examples_list[0].final_cfs_df[feature].values[i] <=
                    permitted_range[feature][1] for i in range(total_CFs))
            else:
                assert all(
                    permitted_range[feature][0] <= ans.cf_examples_list[0].final_cfs_df_sparse[feature].values[i] <=
                    permitted_range[feature][1] for i in range(total_CFs))

    # Testing for 0 CFs needed
    @pytest.mark.parametrize("features_to_vary, desired_class, desired_range, total_CFs, permitted_range",
                             [("all", 0, None, 0, None)])
    def test_zero_cfs_internal(
            self, method, features_to_vary, desired_class, desired_range, sample_custom_query_2, total_CFs,
            permitted_range, custom_public_data_interface, sklearn_binary_classification_model_interface):
        if method == 'genetic':
            pytest.skip('DiceGenetic explainer does not handle the total counterfactuals as zero')
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_binary_classification_model_interface,
            method=method)
        features_to_vary = exp.setup(features_to_vary, None, sample_custom_query_2, "inverse_mad")
        exp._generate_counterfactuals(features_to_vary=features_to_vary, query_instance=sample_custom_query_2,
                                      total_CFs=total_CFs, desired_class=desired_class,
                                      desired_range=desired_range, permitted_range=permitted_range)


@pytest.mark.parametrize("method", ['random', 'genetic', 'kdtree'])
class TestExplainerBaseMultiClassClassification:

    @pytest.mark.parametrize("desired_class", [1])
    def test_zero_totalcfs(
            self, desired_class, method, sample_custom_query_1,
            custom_public_data_interface,
            sklearn_multiclass_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_multiclass_classification_model_interface,
            method=method)
        with pytest.raises(UserConfigValidationException):
            exp.generate_counterfactuals(
                    query_instances=[sample_custom_query_1],
                    total_CFs=0,
                    desired_class=desired_class)

    # Testing that the counterfactuals are in the desired class
    @pytest.mark.parametrize("desired_class, total_CFs", [(2, 2)])
    @pytest.mark.parametrize("genetic_initialization", ['kdtree', 'random'])
    def test_desired_class(
            self, desired_class, total_CFs, method, genetic_initialization,
            sample_custom_query_2,
            custom_public_data_interface,
            sklearn_multiclass_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_multiclass_classification_model_interface,
            method=method)

        if method != 'genetic':
            ans = exp.generate_counterfactuals(
                    query_instances=sample_custom_query_2,
                    total_CFs=total_CFs, desired_class=desired_class)
        else:
            ans = exp.generate_counterfactuals(
                    query_instances=sample_custom_query_2,
                    total_CFs=total_CFs, desired_class=desired_class,
                    initialization=genetic_initialization)

        assert ans is not None
        if method != 'kdtree':
            assert all(
                ans.cf_examples_list[0].final_cfs_df[exp.data_interface.outcome_name].values == [desired_class] * total_CFs)
        else:
            assert all(
                ans.cf_examples_list[0].final_cfs_df_sparse[exp.data_interface.outcome_name].values ==
                [desired_class] * total_CFs)
        assert all(i == desired_class for i in exp.cfs_preds)

    # When no elements in the desired_class are present in the training data
    @pytest.mark.parametrize("desired_class, total_CFs", [(100, 3), ('opposite', 3)])
    def test_unsupported_multiclass(
            self, desired_class, total_CFs, method, sample_custom_query_4,
            custom_public_data_interface,
            sklearn_multiclass_classification_model_interface):
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_multiclass_classification_model_interface,
            method=method)
        with pytest.raises(UserConfigValidationException) as ucve:
            exp.generate_counterfactuals(query_instances=sample_custom_query_4, total_CFs=total_CFs,
                                         desired_class=desired_class)
        if desired_class == 100:
            assert "Desired class not present in training data!" in str(ucve)
        else:
            assert "Desired class cannot be opposite if the number of classes is more than 2." in str(ucve)

    # Testing for 0 CFs needed
    @pytest.mark.parametrize("features_to_vary, desired_class, desired_range, total_CFs, permitted_range",
                             [("all", 0, None, 0, None)])
    def test_zero_cfs_internal(
            self, method, features_to_vary, desired_class, desired_range, sample_custom_query_2, total_CFs,
            permitted_range, custom_public_data_interface, sklearn_multiclass_classification_model_interface):
        if method == 'genetic':
            pytest.skip('DiceGenetic explainer does not handle the total counterfactuals as zero')
        exp = dice_ml.Dice(
            custom_public_data_interface,
            sklearn_multiclass_classification_model_interface,
            method=method)
        features_to_vary = exp.setup(features_to_vary, None, sample_custom_query_2, "inverse_mad")
        exp._generate_counterfactuals(features_to_vary=features_to_vary, query_instance=sample_custom_query_2,
                                      total_CFs=total_CFs, desired_class=desired_class,
                                      desired_range=desired_range, permitted_range=permitted_range)


class TestExplainerBaseRegression:

    @pytest.mark.parametrize("desired_range, regression_exp_object",
                             [([10, 100], 'random'), ([10, 100], 'genetic'), ([10, 100], 'kdtree')],
                             indirect=['regression_exp_object'])
    def test_zero_totalcfs(self, desired_range, regression_exp_object, sample_custom_query_1):
        exp = regression_exp_object  # explainer object
        with pytest.raises(UserConfigValidationException):
            exp.generate_counterfactuals(
                    query_instances=[sample_custom_query_1],
                    total_CFs=0,
                    desired_range=desired_range)

    @pytest.mark.parametrize("desired_range, method",
                             [([10, 100], 'random')])
    def test_numeric_categories(self, desired_range, method, create_boston_data):
        x_train, x_test, y_train, y_test, feature_names = \
            create_boston_data

        rfc = RandomForestRegressor(n_estimators=10, max_depth=4,
                                    random_state=777)
        model = rfc.fit(x_train, y_train)

        dataset_train = x_train.copy()
        dataset_train['Outcome'] = y_train
        feature_names.remove('CHAS')

        d = dice_ml.Data(dataframe=dataset_train, continuous_features=feature_names, outcome_name='Outcome')
        m = dice_ml.Model(model=model, backend='sklearn', model_type='regressor')
        exp = dice_ml.Dice(d, m, method=method)

        cf_explanation = exp.generate_counterfactuals(
            query_instances=x_test.iloc[0:1],
            total_CFs=10,
            desired_range=desired_range)

        assert cf_explanation is not None


class TestExplainerBase:

    def test_instantiating_explainer_base(self, public_data_object):
        with pytest.raises(TypeError):
            ExplainerBase(data_interface=public_data_object)
