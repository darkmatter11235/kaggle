import numpy as np
import pandas as pd
import xgboost as xgb
import gc

def submit(clf, sample, prop, train_columns):

	print('Building test set ...')
	if 'ParcelId' in sample:
		sample['parcelid'] = sample['ParcelId']
		df_test = sample.merge(prop, on='parcelid', how='left')
	else:
		df_test = sample
	del prop; gc.collect()
	x_test = df_test[train_columns]
	for c in x_test.dtypes[x_test.dtypes == object].index.values:
	    x_test[c] = (x_test[c] == True)

	del df_test, sample; gc.collect()

	d_test = xgb.DMatrix(x_test)

	del x_test; gc.collect()

	print('Predicting on test ...')

	p_test = clf.predict(d_test)

	del d_test; gc.collect()

	if 'ParcelId' in sample:
		sub = pd.read_csv('../input/sample_submission.csv')
		for c in sub.columns[sub.columns != 'ParcelId']:
	    		sub[c] = p_test

	print('Writing csv ...')
	sub.to_csv('xgb_starter.csv', index=False, float_format='%.4f') # Thanks to @inversion


def predict_test(clf, sample, prop, train_columns, ref_test):

	print('Building test set ...')
	if 'ParcelId' in sample:
		sample['parcelid'] = sample['ParcelId']
		df_test = sample.merge(prop, on='parcelid', how='left')
	else:
		df_test = sample
	del prop; gc.collect()
	x_test = df_test[train_columns]
	for c in x_test.dtypes[x_test.dtypes == object].index.values:
	    x_test[c] = (x_test[c] == True)

	#del df_test, sample; gc.collect()

	d_test = xgb.DMatrix(x_test)

	del x_test; gc.collect()

	print('Predicting on test ...')

	p_test = clf.predict(d_test)

	del d_test; gc.collect()

	if 'ParcelId' in sample:
		sub = pd.read_csv('../input/sample_submission.csv')
		for c in sub.columns[sub.columns != 'ParcelId']:
	    		sub[c] = p_test

	print('Writing csv ...')
	if ref_test.any():
		for i in range(ref_test.shape[0]):
			print(p_test[i], ref_test[i])
	#sub.to_csv('xgb_starter.csv', index=False, float_format='%.4f') # Thanks to @inversion

print('Loading data ...')

train = pd.read_csv('../input/train_2016.csv', parse_dates=["transactiondate"])
prop = pd.read_csv('../input/properties_2016.csv')
train["transactionday"] = train["transactiondate"].dt.day
train["transactionmonth"] = train["transactiondate"].dt.month
train["transactionyear"] = train["transactiondate"].dt.year
sample = pd.read_csv('../input/sample_submission.csv')

print('Binding to float32')

for c, dtype in zip(prop.columns, prop.dtypes):
	if dtype == np.float64:
		prop[c] = prop[c].astype(np.float32)

print('Creating training set ...')

df_train = train.merge(prop, how='left', on='parcelid')

x_train = df_train.drop(['parcelid', 'logerror', 'transactiondate', 'propertyzoningdesc', 'propertycountylandusecode'], axis=1)
y_train = df_train['logerror'].values
print(x_train.shape, y_train.shape)

train_columns = x_train.columns
#train_columns = ['lotsizesquarefeet', 'transactionday', 'transactionmonth', 'transactionyear', 'taxamount', 'latitude', 'longitude', 'censustractandblock', 'regionidzip']

for c in x_train.dtypes[x_train.dtypes == object].index.values:
    x_train[c] = (x_train[c] == True)

x_train = x_train[train_columns]
print("AFTER")
print(x_train.shape, y_train.shape)
del df_train; gc.collect()

split = 80000
x_train, y_train, x_valid, y_valid = x_train[:split], y_train[:split], x_train[split:], y_train[split:]

print('Building DMatrix...')

d_train = xgb.DMatrix(x_train, label=y_train)
d_valid = xgb.DMatrix(x_valid, label=y_valid)

#del x_train, x_valid; gc.collect()

print('Training ...')

params = {}
params['eta'] = 0.08
params['objective'] = 'reg:linear'
params['eval_metric'] = 'rmse'
params['eval_metric'] = 'mae'
params['max_depth'] = 4
params['silent'] = 1

watchlist = [(d_train, 'train'), (d_valid, 'valid')]
clf = xgb.train(params, d_train, 10000, watchlist, early_stopping_rounds=100, verbose_eval=10)

#predict_test(clf, x_valid, prop, train_columns, y_valid)
predict_test(clf, sample, prop, train_columns)
del d_train, d_valid
