# HRF Convolution

In this tab, you can select which predictors you'd like to convolve with the canonical haemodynamic-response function (HRF).

Typically, you'll want to convolve all non-confounds. You can easily do this by clicking `Select All Non-Confounds`.

As in the `Predictors` tab, you can perform a full-text search over all the predictors you previously selected.

For now, we are applying a ["SPM" style](https://en.wikibooks.org/wiki/SPM/Haemodynamic_Response_Function) HRF, with no derivatives.

![hrf](img/hrf.png)


!!! Note
    In reality, HRF convolution is another transformation that is applied after all other transformations.
    Thus, the transformed variables will be the ones that are convolved.
