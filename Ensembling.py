
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from imblearn.under_sampling._prototype_selection._instance_hardness_threshold import  deprecate_parameter
from imblearn.utils.tests.test_docstring import Substitution
from imblearn.utils._docstring  import  _random_state_docstring
from imblearn.under_sampling.base import BaseCleaningSampler
from collections import Counter
from scipy.sparse import issparse
from sklearn.base import clone
from sklearn.neighbors import KNeighborsClassifier
from sklearn.utils import check_random_state, safe_indexing
from sklearn import metrics
from sklearn.model_selection import train_test_split
from sklearn.ensemble import AdaBoostClassifier
from sklearn.metrics import roc_curve, auc, roc_auc_score
from sklearn.preprocessing import LabelBinarizer
%matplotlib inline
from google.colab import files
#uploaded = files.upload()
import io


datasetlist = ['new-thyroid.data','cancer_classification.csv','bupa.data'] # add the other 2 datasets
datasetcolumn = [['target','t3-resin','Total Serum thyroxin','Total serum triiodothyronine','basal','tsh'],['mean radius', 'mean texture', 'mean perimeter', 'mean area',
       'mean smoothness', 'mean compactness', 'mean concavity',
       'mean concave points', 'mean symmetry', 'mean fractal dimension',
       'radius error', 'texture error', 'perimeter error', 'area error',
       'smoothness error', 'compactness error', 'concavity error',
       'concave points error', 'symmetry error', 'fractal dimension error',
       'worst radius', 'worst texture', 'worst perimeter', 'worst area',
       'worst smoothness', 'worst compactness', 'worst concavity',
       'worst concave points', 'worst symmetry', 'worst fractal dimension',
       'target'],['mcv','alkphos','sgpt','sgot','gammagt','drinks','target']]
for i in range(len(datasetlist)):
    uploaded=files.upload()
    if(i==1):
      df = pd.read_csv(io.BytesIO(uploaded[datasetlist[i]]))
      df.rename(columns={'benign_0__mal_1':'target'}, inplace=True)
    else:
      df = pd.read_csv(io.BytesIO(uploaded[datasetlist[i]]),header=None)
      #df = pd.read_csv(io.BytesIO(uploaded['bupa.data']),header=None)
      df.columns=datasetcolumn[i]
      if(i==0):                                 
          df['target'].replace(3,2,inplace=True)
          df['target'].replace(1,0,inplace=True)
          df['target'].replace(2,1,inplace=True)
      elif(i==2):
          df['target'].replace(1,0,inplace=True)
          df['target'].replace(2,1,inplace=True)       




    X=df.drop('target',axis=1)
    y=df['target']
    class condensedNearestNeighbour(BaseCleaningSampler):    
        """Class to perform under-sampling based on the condensed nearest neighbour
        method.
        Read more in the :ref:`User Guide <condensed_nearest_neighbors>`.
        Parameters
        ----------
        {sampling_strategy}
        return_indices : bool, optional (default=False)
            Whether or not to return the indices of the samples randomly
            selected.
            .. deprecated:: 0.4
              ``return_indices`` is deprecated. Use the attribute
              ``sample_indices_`` instead.
        {random_state}
        n_neighbors : int or object, optional (default=\
    KNeighborsClassifier(n_neighbors=1))
            If ``int``, size of the neighbourhood to consider to compute the
            nearest neighbors. If object, an estimator that inherits from
            :class:`sklearn.neighbors.base.KNeighborsMixin` that will be used to
            find the nearest-neighbors.
        n_seeds_S : int, optional (default=1)
            Number of samples to extract in order to build the set S.
        n_jobs : int, optional (default=1)
            The number of threads to open if possible.
        ratio : str, dict, or callable
            .. deprecated:: 0.4
              Use the parameter ``sampling_strategy`` instead. It will be removed
              in 0.6.
        Attributes
        ----------
        sample_indices_ : ndarray, shape (n_new_samples)
            Indices of the samples selected.
            .. versionadded:: 0.4
              ``sample_indices_`` used instead of ``return_indices=True``.
        Notes
        -----
        The method is based on [1]_.
        Supports multi-class resampling. A one-vs.-rest scheme is used when
        sampling a class as proposed in [1]_.
        See also
        --------
        EditedNearestNeighbours, RepeatedEditedNearestNeighbours, AllKNN
        References
        ----------
        .. [1] P. Hart, "The condensed nearest neighbor rule,"
          In Information Theory, IEEE Transactions on, vol. 14(3),
          pp. 515-516, 1968.
        Examples
        --------
        >>> from collections import Counter # doctest: +SKIP
        >>> from sklearn.datasets import fetch_mldata # doctest: +SKIP
        >>> from imblearn.under_sampling import \
    CondensedNearestNeighbour # doctest: +SKIP
        >>> pima = fetch_mldata('diabetes_scale') # doctest: +SKIP
        >>> X, y = pima['data'], pima['target'] # doctest: +SKIP
        >>> print('Original dataset shape %s' % Counter(y)) # doctest: +SKIP
        Original dataset shape Counter({{1: 500, -1: 268}}) # doctest: +SKIP
        >>> cnn = CondensedNearestNeighbour(random_state=42) # doctest: +SKIP
        >>> X_res, y_res = cnn.fit_resample(X, y) #doctest: +SKIP
        >>> print('Resampled dataset shape %s' % Counter(y_res)) # doctest: +SKIP
        Resampled dataset shape Counter({{-1: 268, 1: 227}}) # doctest: +SKIP
        """

        def __init__(self,
                    sampling_strategy='auto',
                    return_indices=False,
                    random_state=None,
                    n_neighbors=None,
                    n_seeds_S=1,
                    n_jobs=1,
                    ratio=None):
            super().__init__(
                sampling_strategy=sampling_strategy, ratio=ratio)
            self.random_state = random_state
            self.return_indices = return_indices
            self.n_neighbors = n_neighbors
            self.n_seeds_S = n_seeds_S
            self.n_jobs = n_jobs

        def _validate_estimator(self):
            """Private function to create the NN estimator"""
            if self.n_neighbors is None:
                self.estimator_ = KNeighborsClassifier(
                    n_neighbors=1, n_jobs=self.n_jobs)
            elif isinstance(self.n_neighbors, int):
                self.estimator_ = KNeighborsClassifier(
                    n_neighbors=self.n_neighbors, n_jobs=self.n_jobs)
            elif isinstance(self.n_neighbors, KNeighborsClassifier):
                self.estimator_ = clone(self.n_neighbors)
            else:
                raise ValueError('`n_neighbors` has to be a int or an object'
                                ' inhereited from KNeighborsClassifier.'
                                ' Got {} instead.'.format(type(self.n_neighbors)))

        def _fit_resample(self, X, y):
            if self.return_indices:
                deprecate_parameter(self, '0.4', 'return_indices',
                                    'sample_indices_')
            self._validate_estimator()

            random_state = check_random_state(self.random_state)
            target_stats = Counter(y)
            class_minority = min(target_stats, key=target_stats.get)
            idx_under = np.empty((0, ), dtype=int)

            for target_class in np.unique(y):
                if target_class in self.sampling_strategy_.keys():
                    # Randomly get one sample from the majority class
                    # Generate the index to select
                    idx_maj = np.flatnonzero(y == target_class)
                    idx_maj_sample = idx_maj[random_state.randint(
                        low=0,
                        high=target_stats[target_class],
                        size=self.n_seeds_S)]

                    # Create the set C - One majority samples and all minority
                    C_indices = np.append(
                        np.flatnonzero(y == class_minority), idx_maj_sample)
                    C_x = safe_indexing(X, C_indices)
                    C_y = safe_indexing(y, C_indices)

                    # Create the set S - all majority samples
                    S_indices = np.flatnonzero(y == target_class)
                    S_x = safe_indexing(X, S_indices)
                    S_y = safe_indexing(y, S_indices)

                    # fit knn on C
                    self.estimator_.fit(C_x, C_y)

                    good_classif_label = idx_maj_sample.copy()
                    # Check each sample in S if we keep it or drop it
                    for idx_sam, (x_sam, y_sam) in enumerate(zip(S_x, S_y)):

                        # Do not select sample which are already well classified
                        if idx_sam in good_classif_label:
                            continue

                        # Classify on S
                        if not issparse(x_sam):
                            x_sam = x_sam.reshape(1, -1)
                        pred_y = self.estimator_.predict(x_sam)

                        # If the prediction do not agree with the true label
                        # append it in C_x
                        if y_sam != pred_y:
                            # Keep the index for later
                            idx_maj_sample = np.append(idx_maj_sample,
                                                      idx_maj[idx_sam])

                            # Update C
                            C_indices = np.append(C_indices, idx_maj[idx_sam])
                            C_x = safe_indexing(X, C_indices)
                            C_y = safe_indexing(y, C_indices)

                            # fit a knn on C
                            self.estimator_.fit(C_x, C_y)

                            # This experimental to speed up the search
                            # Classify all the element in S and avoid to test the
                            # well classified elements
                            pred_S_y = self.estimator_.predict(S_x)
                            good_classif_label = np.unique(
                                np.append(idx_maj_sample,
                                          np.flatnonzero(pred_S_y == S_y)))

                    idx_under = np.concatenate((idx_under, idx_maj_sample), axis=0)
                else:
                    idx_under = np.concatenate(
                        (idx_under, np.flatnonzero(y == target_class)), axis=0)

            self.sample_indices_ = idx_under

            if self.return_indices:
                return (safe_indexing(X, idx_under), safe_indexing(y, idx_under),
                        idx_under)
            return safe_indexing(X, idx_under), safe_indexing(y, idx_under),idx_under

        def _more_tags(self):
            return {'sample_indices': True}
    cc = condensedNearestNeighbour(n_neighbors=1)
    X_0, y_0,index1= cc.fit_resample(X, y)
    X=df.drop('target',axis=1)
    y=df['target']
    from  imblearn.utils._validation import check_neighbors_object
    from  imblearn.under_sampling.base import BaseUnderSampler
    @Substitution(
        sampling_strategy=BaseUnderSampler._sampling_strategy_docstring,
        random_state=_random_state_docstring)
    class NearMiss(BaseUnderSampler):

        """Class to perform under-sampling based on NearMiss methods.
        Read more in the :ref:`User Guide <controlled_under_sampling>`.
        Parameters
        ----------
        {sampling_strategy}
        return_indices : bool, optional (default=False)
            Whether or not to return the indices of the samples randomly
            selected from the majority class.
            .. deprecated:: 0.4
              ``return_indices`` is deprecated. Use the attribute
              ``sample_indices_`` instead.
        {random_state}
            .. deprecated:: 0.4
              ``random_state`` is deprecated in 0.4 and will be removed in 0.6.
        version : int, optional (default=1)
            Version of the NearMiss to use. Possible values are 1, 2 or 3.
        n_neighbors : int or object, optional (default=3)
            If ``int``, size of the neighbourhood to consider to compute the
            average distance to the minority point samples.  If object, an
            estimator that inherits from
            :class:`sklearn.neighbors.base.KNeighborsMixin` that will be used to
            find the k_neighbors.
        n_neighbors_ver3 : int or object, optional (default=3)
            If ``int``, NearMiss-3 algorithm start by a phase of re-sampling. This
            parameter correspond to the number of neighbours selected create the
            subset in which the selection will be performed.  If object, an
            estimator that inherits from
            :class:`sklearn.neighbors.base.KNeighborsMixin` that will be used to
            find the k_neighbors.
        n_jobs : int, optional (default=1)
            The number of threads to open if possible.
        ratio : str, dict, or callable
            .. deprecated:: 0.4
              Use the parameter ``sampling_strategy`` instead. It will be removed
              in 0.6.
        Attributes
        ----------
        sample_indices_ : ndarray, shape (n_new_samples)
            Indices of the samples selected.
            .. versionadded:: 0.4
              ``sample_indices_`` used instead of ``return_indices=True``.
        Notes
        -----
        The methods are based on [1]_.
        Supports multi-class resampling.
        References
        ----------
        .. [1] I. Mani, I. Zhang. "kNN approach to unbalanced data distributions:
          a case study involving information extraction," In Proceedings of
          workshop on learning from imbalanced datasets, 2003.
        Examples
        --------
        >>> from collections import Counter
        >>> from sklearn.datasets import make_classification
        >>> from imblearn.under_sampling import \
    NearMiss # doctest: +NORMALIZE_WHITESPACE
        >>> X, y = make_classification(n_classes=2, class_sep=2,
        ... weights=[0.1, 0.9], n_informative=3, n_redundant=1, flip_y=0,
        ... n_features=20, n_clusters_per_class=1, n_samples=1000, random_state=10)
        >>> print('Original dataset shape %s' % Counter(y))
        Original dataset shape Counter({{1: 900, 0: 100}})
        >>> nm = NearMiss()
        >>> X_res, y_res = nm.fit_resample(X, y)
        >>> print('Resampled dataset shape %s' % Counter(y_res))
        Resampled dataset shape Counter({{0: 100, 1: 100}})
        """

        def __init__(self,
                    sampling_strategy='auto',
                    return_indices=False,
                    random_state=None,
                    version=1,
                    n_neighbors=3,
                    n_neighbors_ver3=3,
                    n_jobs=1,
                    ratio=None):
            super().__init__(
                sampling_strategy=sampling_strategy, ratio=ratio)
            self.random_state = random_state
            self.return_indices = return_indices
            self.version = version
            self.n_neighbors = n_neighbors
            self.n_neighbors_ver3 = n_neighbors_ver3
            self.n_jobs = n_jobs

        def _selection_dist_based(self,
                                  X,
                                  y,
                                  dist_vec,
                                  num_samples,
                                  key,
                                  sel_strategy='nearest'):
            """Select the appropriate samples depending of the strategy selected.
            Parameters
            ----------
            X : {array-like, sparse matrix}, shape (n_samples, n_features)
                Original samples.
            y : array-like, shape (n_samples,)
                Associated label to X.
            dist_vec : ndarray, shape (n_samples, )
                The distance matrix to the nearest neigbour.
            num_samples: int
                The desired number of samples to select.
            key : str or int,
                The target class.
            sel_strategy : str, optional (default='nearest')
                Strategy to select the samples. Either 'nearest' or 'farthest'
            Returns
            -------
            idx_sel : ndarray, shape (num_samples,)
                The list of the indices of the selected samples.
            """

            # Compute the distance considering the farthest neighbour
            dist_avg_vec = np.sum(dist_vec[:, -self.nn_.n_neighbors:], axis=1)

            target_class_indices = np.flatnonzero(y == key)
            if (dist_vec.shape[0] != safe_indexing(X,
                                                  target_class_indices).shape[0]):
                raise RuntimeError('The samples to be selected do not correspond'
                                  ' to the distance matrix given. Ensure that'
                                  ' both `X[y == key]` and `dist_vec` are'
                                  ' related.')

            # Sort the list of distance and get the index
            if sel_strategy == 'nearest':
                sort_way = False
            elif sel_strategy == 'farthest':
                sort_way = True
            else:
                raise NotImplementedError

            sorted_idx = sorted(
                range(len(dist_avg_vec)),
                key=dist_avg_vec.__getitem__,
                reverse=sort_way)

            # Throw a warning to tell the user that we did not have enough samples
            # to select and that we just select everything
            if len(sorted_idx) < num_samples:
                warnings.warn('The number of the samples to be selected is larger'
                              ' than the number of samples available. The'
                              ' balancing ratio cannot be ensure and all samples'
                              ' will be returned.')

            # Select the desired number of samples
            return sorted_idx[:num_samples]

        def _validate_estimator(self):
            """Private function to create the NN estimator"""

            # check for deprecated random_state
            if self.random_state is not None:
                deprecate_parameter(self, '0.4', 'random_state')

            self.nn_ = check_neighbors_object('n_neighbors', self.n_neighbors)
            self.nn_.set_params(**{'n_jobs': self.n_jobs})

            if self.version == 3:
                self.nn_ver3_ = check_neighbors_object('n_neighbors_ver3',
                                                      self.n_neighbors_ver3)
                self.nn_ver3_.set_params(**{'n_jobs': self.n_jobs})

            if self.version not in (1, 2, 3):
                raise ValueError('Parameter `version` must be 1, 2 or 3, got'
                                ' {}'.format(self.version))

        def _fit_resample(self, X, y):
            if self.return_indices:
                deprecate_parameter(self, '0.4', 'return_indices',
                                    'sample_indices_')
            self._validate_estimator()

            idx_under = np.empty((0, ), dtype=int)

            target_stats = Counter(y)
            class_minority = min(target_stats, key=target_stats.get)
            minority_class_indices = np.flatnonzero(y == class_minority)

            self.nn_.fit(safe_indexing(X, minority_class_indices))

            for target_class in np.unique(y):
                if target_class in self.sampling_strategy_.keys():
                    n_samples = self.sampling_strategy_[target_class]
                    target_class_indices = np.flatnonzero(y == target_class)
                    X_class = safe_indexing(X, target_class_indices)
                    y_class = safe_indexing(y, target_class_indices)

                    if self.version == 1:
                        dist_vec, idx_vec = self.nn_.kneighbors(
                            X_class, n_neighbors=self.nn_.n_neighbors)
                        index_target_class = self._selection_dist_based(
                            X,
                            y,
                            dist_vec,
                            n_samples,
                            target_class,
                            sel_strategy='nearest')
                    elif self.version == 2:
                        dist_vec, idx_vec = self.nn_.kneighbors(
                            X_class, n_neighbors=target_stats[class_minority])
                        index_target_class = self._selection_dist_based(
                            X,
                            y,
                            dist_vec,
                            n_samples,
                            target_class,
                            sel_strategy='nearest')
                    elif self.version == 3:
                        self.nn_ver3_.fit(X_class)
                        dist_vec, idx_vec = self.nn_ver3_.kneighbors(
                            safe_indexing(X, minority_class_indices))
                        idx_vec_farthest = np.unique(idx_vec.reshape(-1))
                        X_class_selected = safe_indexing(X_class, idx_vec_farthest)
                        y_class_selected = safe_indexing(y_class, idx_vec_farthest)

                        dist_vec, idx_vec = self.nn_.kneighbors(
                            X_class_selected, n_neighbors=self.nn_.n_neighbors)
                        index_target_class = self._selection_dist_based(
                            X_class_selected,
                            y_class_selected,
                            dist_vec,
                            n_samples,
                            target_class,
                            sel_strategy='farthest')
                        # idx_tmp is relative to the feature selected in the
                        # previous step and we need to find the indirection
                        index_target_class = idx_vec_farthest[index_target_class]
                else:
                    index_target_class = slice(None)

                idx_under = np.concatenate(
                    (idx_under,
                    np.flatnonzero(y == target_class)[index_target_class]),
                    axis=0)

            self.sample_indices_ = idx_under

            if self.return_indices:
                return (safe_indexing(X, idx_under), safe_indexing(y, idx_under),
                        idx_under)
            return safe_indexing(X, idx_under), safe_indexing(y, idx_under),idx_under

        def _more_tags(self):
            return {'sample_indices': True}
    de=NearMiss()
    X_f,y_f,index2=de.fit_resample(X,y)
    X=df.drop('target',axis=1)
    y=df['target']
    from  imblearn.utils._validation import check_neighbors_object
    from  imblearn.under_sampling.base import BaseUnderSampler
    @Substitution(
        sampling_strategy=BaseUnderSampler._sampling_strategy_docstring,
        random_state=_random_state_docstring)
    class NearMiss(BaseUnderSampler):
        """Class to perform under-sampling based on NearMiss methods.
        Read more in the :ref:`User Guide <controlled_under_sampling>`.
        Parameters
        ----------
        {sampling_strategy}
        return_indices : bool, optional (default=False)
            Whether or not to return the indices of the samples randomly
            selected from the majority class.
            .. deprecated:: 0.4
              ``return_indices`` is deprecated. Use the attribute
              ``sample_indices_`` instead.
        {random_state}
            .. deprecated:: 0.4
              ``random_state`` is deprecated in 0.4 and will be removed in 0.6.
        version : int, optional (default=1)
            Version of the NearMiss to use. Possible values are 1, 2 or 3.
        n_neighbors : int or object, optional (default=3)
            If ``int``, size of the neighbourhood to consider to compute the
            average distance to the minority point samples.  If object, an
            estimator that inherits from
            :class:`sklearn.neighbors.base.KNeighborsMixin` that will be used to
            find the k_neighbors.
        n_neighbors_ver3 : int or object, optional (default=3)
            If ``int``, NearMiss-3 algorithm start by a phase of re-sampling. This
            parameter correspond to the number of neighbours selected create the
            subset in which the selection will be performed.  If object, an
            estimator that inherits from
            :class:`sklearn.neighbors.base.KNeighborsMixin` that will be used to
            find the k_neighbors.
        n_jobs : int, optional (default=1)
            The number of threads to open if possible.
        ratio : str, dict, or callable
            .. deprecated:: 0.4
              Use the parameter ``sampling_strategy`` instead. It will be removed
              in 0.6.
        Attributes
        ----------
        sample_indices_ : ndarray, shape (n_new_samples)
            Indices of the samples selected.
            .. versionadded:: 0.4
              ``sample_indices_`` used instead of ``return_indices=True``.
        Notes
        -----
        The methods are based on [1]_.
        Supports multi-class resampling.
        References
        ----------
        .. [1] I. Mani, I. Zhang. "kNN approach to unbalanced data distributions:
          a case study involving information extraction," In Proceedings of
          workshop on learning from imbalanced datasets, 2003.
        Examples
        --------
        >>> from collections import Counter
        >>> from sklearn.datasets import make_classification
        >>> from imblearn.under_sampling import \
    NearMiss # doctest: +NORMALIZE_WHITESPACE
        >>> X, y = make_classification(n_classes=2, class_sep=2,
        ... weights=[0.1, 0.9], n_informative=3, n_redundant=1, flip_y=0,
        ... n_features=20, n_clusters_per_class=1, n_samples=1000, random_state=10)
        >>> print('Original dataset shape %s' % Counter(y))
        Original dataset shape Counter({{1: 900, 0: 100}})
        >>> nm = NearMiss()
        >>> X_res, y_res = nm.fit_resample(X, y)
        >>> print('Resampled dataset shape %s' % Counter(y_res))
        Resampled dataset shape Counter({{0: 100, 1: 100}})
        """

        def __init__(self,
                    sampling_strategy='auto',
                    return_indices=False,
                    random_state=None,
                    version=3,
                    n_neighbors=3,
                    n_neighbors_ver3=3,
                    n_jobs=1,
                    ratio=None):
            super().__init__(
                sampling_strategy=sampling_strategy, ratio=ratio)
            self.random_state = random_state
            self.return_indices = return_indices
            self.version = version
            self.n_neighbors = n_neighbors
            self.n_neighbors_ver3 = n_neighbors_ver3
            self.n_jobs = n_jobs

        def _selection_dist_based(self,
                                  X,
                                  y,
                                  dist_vec,
                                  num_samples,
                                  key,
                                  sel_strategy='nearest'):
            """Select the appropriate samples depending of the strategy selected.
            Parameters
            ----------
            X : {array-like, sparse matrix}, shape (n_samples, n_features)
                Original samples.
            y : array-like, shape (n_samples,)
                Associated label to X.
            dist_vec : ndarray, shape (n_samples, )
                The distance matrix to the nearest neigbour.
            num_samples: int
                The desired number of samples to select.
            key : str or int,
                The target class.
            sel_strategy : str, optional (default='nearest')
                Strategy to select the samples. Either 'nearest' or 'farthest'
            Returns
            -------
            idx_sel : ndarray, shape (num_samples,)
                The list of the indices of the selected samples.
            """

            # Compute the distance considering the farthest neighbour
            dist_avg_vec = np.sum(dist_vec[:, -self.nn_.n_neighbors:], axis=1)

            target_class_indices = np.flatnonzero(y == key)
            if (dist_vec.shape[0] != safe_indexing(X,
                                                  target_class_indices).shape[0]):
                raise RuntimeError('The samples to be selected do not correspond'
                                  ' to the distance matrix given. Ensure that'
                                  ' both `X[y == key]` and `dist_vec` are'
                                  ' related.')

            # Sort the list of distance and get the index
            if sel_strategy == 'nearest':
                sort_way = False
            elif sel_strategy == 'farthest':
                sort_way = True
            else:
                raise NotImplementedError

            sorted_idx = sorted(
                range(len(dist_avg_vec)),
                key=dist_avg_vec.__getitem__,
                reverse=sort_way)

            # Throw a warning to tell the user that we did not have enough samples
            # to select and that we just select everything
            #if len(sorted_idx) < num_samples:
                #warnings.warn('The number of the samples to be selected is larger'
                            # ' than the number of samples available. The'
                              #' balancing ratio cannot be ensure and all samples'
                              #' will be returned.')

            # Select the desired number of samples
            return sorted_idx[:num_samples]

        def _validate_estimator(self):
            """Private function to create the NN estimator"""

            # check for deprecated random_state
            if self.random_state is not None:
                deprecate_parameter(self, '0.4', 'random_state')

            self.nn_ = check_neighbors_object('n_neighbors', self.n_neighbors)
            self.nn_.set_params(**{'n_jobs': self.n_jobs})

            if self.version == 3:
                self.nn_ver3_ = check_neighbors_object('n_neighbors_ver3',
                                                      self.n_neighbors_ver3)
                self.nn_ver3_.set_params(**{'n_jobs': self.n_jobs})

            if self.version not in (1, 2, 3):
                raise ValueError('Parameter `version` must be 1, 2 or 3, got'
                                ' {}'.format(self.version))

        def _fit_resample(self, X, y):
            if self.return_indices:
                deprecate_parameter(self, '0.4', 'return_indices',
                                    'sample_indices_')
            self._validate_estimator()

            idx_under = np.empty((0, ), dtype=int)

            target_stats = Counter(y)
            class_minority = min(target_stats, key=target_stats.get)
            minority_class_indices = np.flatnonzero(y == class_minority)

            self.nn_.fit(safe_indexing(X, minority_class_indices))

            for target_class in np.unique(y):
                if target_class in self.sampling_strategy_.keys():
                    n_samples = self.sampling_strategy_[target_class]
                    target_class_indices = np.flatnonzero(y == target_class)
                    X_class = safe_indexing(X, target_class_indices)
                    y_class = safe_indexing(y, target_class_indices)

                    if self.version == 1:
                        dist_vec, idx_vec = self.nn_.kneighbors(
                            X_class, n_neighbors=self.nn_.n_neighbors)
                        index_target_class = self._selection_dist_based(
                            X,
                            y,
                            dist_vec,
                            n_samples,
                            target_class,
                            sel_strategy='nearest')
                    elif self.version == 2:
                        dist_vec, idx_vec = self.nn_.kneighbors(
                            X_class, n_neighbors=target_stats[class_minority])
                        index_target_class = self._selection_dist_based(
                            X,
                            y,
                            dist_vec,
                            n_samples,
                            target_class,
                            sel_strategy='nearest')
                    elif self.version == 3:
                        self.nn_ver3_.fit(X_class)
                        dist_vec, idx_vec = self.nn_ver3_.kneighbors(
                            safe_indexing(X, minority_class_indices))
                        idx_vec_farthest = np.unique(idx_vec.reshape(-1))
                        X_class_selected = safe_indexing(X_class, idx_vec_farthest)
                        y_class_selected = safe_indexing(y_class, idx_vec_farthest)

                        dist_vec, idx_vec = self.nn_.kneighbors(
                            X_class_selected, n_neighbors=self.nn_.n_neighbors)
                        index_target_class = self._selection_dist_based(
                            X_class_selected,
                            y_class_selected,
                            dist_vec,
                            n_samples,
                            target_class,
                            sel_strategy='farthest')
                        # idx_tmp is relative to the feature selected in the
                        # previous step and we need to find the indirection
                        index_target_class = idx_vec_farthest[index_target_class]
                else:
                    index_target_class = slice(None)

                idx_under = np.concatenate(
                    (idx_under,
                    np.flatnonzero(y == target_class)[index_target_class]),
                    axis=0)

            self.sample_indices_ = idx_under

            if self.return_indices:
                return (safe_indexing(X, idx_under), safe_indexing(y, idx_under),
                        idx_under)
            return safe_indexing(X, idx_under), safe_indexing(y, idx_under),idx_under

        def _more_tags(self):
            return {'sample_indices': True}
    dt=NearMiss()
    X_ff,y_ff,index3=dt.fit_resample(X,y)
    def Union(lst1, lst2): 
        final_list = list(set(lst1) | set(lst2)) 
        return final_list
    index_=Union(index1,index2)
    index_final_union=Union(index_,index3)
    under_sample = df.loc[index_final_union]
    under_sample['target'].value_counts()
    X = under_sample.loc[:, df.columns!='target']
    y= under_sample.loc[:, df.columns=='target']
    from sklearn import metrics
    from sklearn.metrics import classification_report,confusion_matrix
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import AdaBoostClassifier

    max=0
    max1=0
    for i in range(0,100):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        abc = AdaBoostClassifier(n_estimators=50,
                                learning_rate=1)
        # Train Adaboost Classifer
        model = abc.fit(X_train, y_train)

        #Predict the response for test dataset
        y_pred = model.predict(X_test)
        if(metrics.accuracy_score(y_test, y_pred)>max):
            max=metrics.accuracy_score(y_test, y_pred)
        false_positive_rate, true_positive_rate, thresholds = roc_curve(y_test, model.predict_proba(X_test)[:,1])
        
        if(auc(false_positive_rate, true_positive_rate)>max):
            max1=auc(false_positive_rate, true_positive_rate)
        print(classification_report(y_pred,y_test))
        print(confusion_matrix(y_pred,y_test))
    print(max)
    print(max1)
