# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 11:10:01 2026

Updated on Mon Apr 27 13:12:31 2026

@author: Alessandra Introvaia
"""

import numpy as np
from scipy.stats import pearsonr
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.feature_selection import f_classif, mutual_info_classif
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (
    balanced_accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)

import pandas as pd


class Ant:
    def __init__(self):
        self.feature_path = []
        self.best_cost = np.inf


class AdaptiveACOFeatureSelector:
    def __init__(
        self,
        X,
        y,
        feature_names,
        heuristic_weights,
        estimator=None,
        n_ants=5,
        iterations=150,
        alpha=1.0,
        beta=2.0,
        initial_pheromone=0.5,
        evaporation_rate=0.2,
        q_constant=1.0,
        min_features=2,
        max_features=None,
        lambda_score=0.90,
        delta_window=3,
        scoring="balanced_accuracy",
        cv_splits=5,
        random_state=42,
    ):
        self.X = np.asarray(X)
        self.y = np.asarray(y)
        self.feature_names = list(feature_names)
        self.n_total_features = self.X.shape[1]

        self.estimator = estimator if estimator is not None else KNeighborsClassifier(n_neighbors=5)
        self.n_ants = n_ants
        self.iterations = iterations
        self.alpha = alpha
        self.beta = beta
        self.initial_pheromone = initial_pheromone
        self.evaporation_rate = evaporation_rate
        self.q_constant = q_constant
        self.min_features = min_features
        self.max_features = max_features if max_features is not None else self.n_total_features
        self.lambda_score = lambda_score
        self.delta_window = delta_window
        self.scoring = scoring
        self.cv_splits = cv_splits
        self.random_state = random_state
        self.rng = np.random.default_rng(random_state)

        self.heuristic_weights = np.asarray(heuristic_weights, dtype=float)
        self.heuristic_weights = np.maximum(self.heuristic_weights, 1e-12)
        self.heuristic_weights = self.heuristic_weights / self.heuristic_weights.sum()

        self.feature_pheromone = np.full(self.n_total_features, self.initial_pheromone, dtype=float)
        self.ants = [Ant() for _ in range(self.n_ants)]

        self.best_features_ = None
        self.best_cost_ = np.inf
        self.best_cv_score_ = -np.inf
        self.curve_ = []
        self.history_ = []

    def _make_cv(self):
        return StratifiedKFold(
            n_splits=self.cv_splits,
            shuffle=True,
            random_state=self.random_state
        )

    def _cv_score(self, feature_idx):
        feature_idx = np.array(feature_idx, dtype=int)
        X_sel = self.X[:, feature_idx]
        cv = self._make_cv()
        scores = cross_val_score(
            self.estimator,
            X_sel,
            self.y,
            cv=cv,
            scoring=self.scoring
        )
        return float(np.mean(scores))

    def _objective(self, feature_idx):
        """
        Cost function to minimize.

        cost(S) = lambda * (1 - CV_score(S)) + (1 - lambda) * (|S| / p)

        where:
        - CV_score(S) is the cross-validated balanced accuracy (or chosen metric)
        - |S| is the number of selected features
        - p is the total number of available features
        """
        if len(feature_idx) == 0:
            return np.inf, -np.inf

        cv_score = self._cv_score(feature_idx)
        size_penalty = len(feature_idx) / self.n_total_features

        cost = self.lambda_score * (1.0 - cv_score) + (1.0 - self.lambda_score) * size_penalty
        return float(cost), float(cv_score)

    def _adaptive_stop_probability(self, recent_mean_delta):
        """
        recent_mean_delta > 0 means improvement, because:
        delta = current_cost - trial_cost
        """
        if recent_mean_delta <= 0:
            return 0.95
        if recent_mean_delta < 0.002:
            return 0.75
        if recent_mean_delta < 0.010:
            return 0.35
        return 0.10

    def _choose_start_feature(self, top_seed_idx, ant_index):
        if ant_index < len(top_seed_idx):
            return int(top_seed_idx[ant_index])
        return int(self.rng.choice(np.arange(self.n_total_features), p=self.heuristic_weights))

    def _build_subset_for_ant(self, ant_index, top_seed_idx):
        ant = Ant()
        start_feature = self._choose_start_feature(top_seed_idx, ant_index)
        ant.feature_path = [start_feature]

        current_cost, current_cv = self._objective(ant.feature_path)
        ant.best_cost = current_cost
        deltas = []

        available = np.setdiff1d(np.arange(self.n_total_features), ant.feature_path)

        while len(available) > 0 and len(ant.feature_path) < self.max_features:
            weights = (
                (self.feature_pheromone[available] ** self.alpha)
                * (self.heuristic_weights[available] ** self.beta)
            )
            weights = np.maximum(weights, 1e-12)
            probs = weights / weights.sum()

            next_feature = int(self.rng.choice(available, p=probs))
            trial_subset = ant.feature_path + [next_feature]

            trial_cost, trial_cv = self._objective(trial_subset)

            # Positive delta means improvement because cost decreased
            delta = current_cost - trial_cost
            deltas.append(delta)

            ant.feature_path = trial_subset
            current_cost = trial_cost
            current_cv = trial_cv
            ant.best_cost = current_cost

            available = available[available != next_feature]

            if len(ant.feature_path) >= self.min_features:
                recent_mean_delta = float(np.mean(deltas[-self.delta_window:]))
                p_stop = self._adaptive_stop_probability(recent_mean_delta)
                if self.rng.random() < p_stop:
                    break

        return ant, current_cost, current_cv

    def fit(self):
        top_seed_idx = np.argsort(self.heuristic_weights)[::-1][:min(5, self.n_total_features)]

        for it in range(1, self.iterations + 1):
            colony_cost = []
            colony_cv = []
            colony_paths = []
            self.ants = []

            for ant_idx in range(self.n_ants):
                ant, cost, cv_score = self._build_subset_for_ant(ant_idx, top_seed_idx)
                self.ants.append(ant)
                colony_cost.append(cost)
                colony_cv.append(cv_score)
                colony_paths.append(ant.feature_path)

                if cost < self.best_cost_:
                    self.best_cost_ = cost
                    self.best_cv_score_ = cv_score
                    self.best_features_ = ant.feature_path.copy()

            # Evaporation
            self.feature_pheromone *= (1.0 - self.evaporation_rate)

            # Deposit pheromone using best ant of the iteration (minimum cost)
            best_idx = int(np.argmin(colony_cost))
            best_path = colony_paths[best_idx]
            best_cost_iter = colony_cost[best_idx]

            deposit = self.q_constant / (best_cost_iter + 1e-10)
            for f in best_path:
                self.feature_pheromone[f] += deposit

            self.curve_.append(self.best_cost_)
            self.history_.append({
                "iteration": it,
                "best_iteration_cost": float(np.min(colony_cost)),
                "mean_iteration_cost": float(np.mean(colony_cost)),
                "global_best_cost": float(self.best_cost_),
                "global_best_cv_score": float(self.best_cv_score_),
                "selected_features_global_best": int(len(self.best_features_)),
            })

        self.history_ = pd.DataFrame(self.history_)
        return self

    def get_selected_indices(self):
        return np.array(self.best_features_, dtype=int)

    def get_selected_feature_names(self):
        return [self.feature_names[i] for i in self.get_selected_indices()]