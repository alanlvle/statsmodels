# coding: utf-8

# DO NOT EDIT
# Autogenerated from the notebook contrasts.ipynb.
# Edit the notebook and then sync the output with this file.
#
# flake8: noqa
# DO NOT EDIT

# # 对比概述 

import numpy as np
import statsmodels.api as sm

# 本文档主要基于 UCLA 的出色资源
# http://www.ats.ucla.edu/stat/r/library/contrast_coding.htm

# K个类别或级别的分类变量通常以K-1个哑变量组进入回归。这相当于水平均值的线性假设。也就是说，
# 这些变量的每个检验统计量等同于检验该水平的平均值在统计上与基本类别的平均值是否显着不同。
# 这种虚拟编码在R术语中称为“处理编码”，我们将遵循此约定。但是，存在不同的编码方法，这些编码
# 方法等于不同的线性假设集。

# 实际上，虚拟编码在技术上不是对比度编码。这是因为哑变量增加一，并且在功能上不独立于模型的截距。
# 另一方面，具有k级分类变量的一组* contrasts *是一组k_k个因子水平均值的函数独立线性组合，它们
# 也独立于虚拟变量之和。虚拟编码本身不是错误的*。它捕获了所有系数，但是当模型假设系数独立时
# （例如在ANOVA中），会使问题复杂化。线性回归模型不假设系数的独立性，因此在这种情况下，
# 通常仅采用虚拟编码。

# 要查看Patsy中的对比度矩阵，我们将使用UCLA ATS的数据。首先，让我们加载数据。

# #### 示例数据

import pandas as pd
url = 'https://stats.idre.ucla.edu/stat/data/hsb2.csv'
hsb2 = pd.read_table(url, delimiter=",")

hsb2.head(10)

# 观测每个种族水平的因变量均值是有意义的（（1 =西班牙裔，2 =亚洲，3 =非裔美国人，4 =高加索人））。

hsb2.groupby('race')['write'].mean()

# #### 处理 (虚拟) 编码

# 虚拟编码可能是最著名的编码方案。 它将分类变量的每个级别与基本参考级别进行比较。 基本参考级别是截距的值。
# 这是Patsy中无序分类因素的默认对比。 处理种族对比矩阵为

from patsy.contrasts import Treatment
levels = [1, 2, 3, 4]
contrast = Treatment(reference=0).code_without_intercept(levels)
print(contrast.matrix)

# 在这里，我们使用“ reference = 0”，这意味着第一个级别（西班牙裔）是衡量其他级别影响的参考类别。 如上所述，
# 列的总和不为零，因此与截距无关。 明确地说，让我们看一下它如何编码`race`变量。


hsb2.race.head(10)

print(contrast.matrix[hsb2.race - 1, :][:20])

sm.categorical(hsb2.race.values)

# 这是一个技巧，因为种族类别可以方便地映射到 zero-based 的索引。 如果不这样做，那么这种转换将在幕后进行，
# 因此这通常不会起作用，但是仍然修正想法是有用的练习。 下面说明了使用上面三个对比的输出


from statsmodels.formula.api import ols
mod = ols("write ~ C(race, Treatment)", data=hsb2)
res = mod.fit()
print(res.summary())

# 我们明确给出了种族的参照。 但是，由于 Treatment 是默认的，因此我们可以省略此设置。

# ### Simple 编码

# 与处理编码类似，简单编码将每个级别与固定参考级别进行对比。 但是，使用简单编码，截距是所有因素水平的总和。
#  Patsy 没有包含简单参照，但是您可以定义自己的参照。 为此，编写一个包含 code_with_intercept 和 
# code_without_intercept 方法的类，该方法返回 patsy.contrast.ContrastMatrix 实例。

from patsy.contrasts import ContrastMatrix


def _name_levels(prefix, levels):
    return ["[%s%s]" % (prefix, level) for level in levels]


class Simple(object):
    def _simple_contrast(self, levels):
        nlevels = len(levels)
        contr = -1. / nlevels * np.ones((nlevels, nlevels - 1))
        contr[1:][np.diag_indices(nlevels - 1)] = (nlevels - 1.) / nlevels
        return contr

    def code_with_intercept(self, levels):
        contrast = np.column_stack((np.ones(len(levels)),
                                    self._simple_contrast(levels)))
        return ContrastMatrix(contrast, _name_levels("Simp.", levels))

    def code_without_intercept(self, levels):
        contrast = self._simple_contrast(levels)
        return ContrastMatrix(contrast, _name_levels("Simp.", levels[:-1]))


hsb2.groupby('race')['write'].mean().mean()

contrast = Simple().code_without_intercept(levels)
print(contrast.matrix)

mod = ols("write ~ C(race, Simple)", data=hsb2)
res = mod.fit()
print(res.summary())

# ### Sum (Deviation) 编码

# 求和编码将给定级别的因变量的平均值与所有级别上因变量的总体平均值进行比较。 也就是说，它使用了第一个 k-1 级别
# 和每个级别 k 之间进行对比。在此示例中，级别 1 与所有其他级别进行比较，级别 2 与所有其他级别进行比较，级别 3 与所有其他级别进行比较。

from patsy.contrasts import Sum
contrast = Sum().code_without_intercept(levels)
print(contrast.matrix)

mod = ols("write ~ C(race, Sum)", data=hsb2)
res = mod.fit()
print(res.summary())

# 这与强制所有系数的总和为零的参数化相对应。 请注意，此处的截距是均值，其中均值是每个级别的因变量均值的均值。

hsb2.groupby('race')['write'].mean().mean()

# ### 后向差分编码

# 在后向差分编码中，将一个级别的因变量的平均值与先前级别的因变量的平均值进行比较。 这种类型的编码对于分类或
# 有序变量可能很有用。

from patsy.contrasts import Diff
contrast = Diff().code_without_intercept(levels)
print(contrast.matrix)

mod = ols("write ~ C(race, Diff)", data=hsb2)
res = mod.fit()
print(res.summary())

# 例如，此处关于级别1的系数是级别2的 “write” 的平均值，而不是级别1的平均值。

res.params["C(race, Diff)[D.1]"]
hsb2.groupby('race').mean()["write"][2] - hsb2.groupby(
    'race').mean()["write"][1]

# ### Helmert 编码

# 我们的 Helmert 编码版本有时被称为反向 Helmert 编码。 将某个级别的因变量的平均值与所有先前级别的因变量的平均值进行比较。
# 因此，有时使用 'reverse' 这个名称来区别于正向 Helmert 编码。 对于分类变量（例如 race），这种比较没有多大意义，但是我们将
# 使用 Helmert 对比，如下所示：


from patsy.contrasts import Helmert
contrast = Helmert().code_without_intercept(levels)
print(contrast.matrix)

mod = ols("write ~ C(race, Helmert)", data=hsb2)
res = mod.fit()
print(res.summary())

# 为了说明这一点，第4级的参照是前三个级别的因变量的平均值，取自第4级的平均值

grouped = hsb2.groupby('race')
grouped.mean()["write"][4] - grouped.mean()["write"][:3].mean()

# 如您所见，这些仅等于一个常数。 Helmert对比的其他版本给出了实际的均值差异。 无论如何，假设检验是相同的。

k = 4
1. / k * (grouped.mean()["write"][k] - grouped.mean()["write"][:k - 1].mean())
k = 3
1. / k * (grouped.mean()["write"][k] - grouped.mean()["write"][:k - 1].mean())

# ### 正交多项式编码

# 通过多项式编码对“ k = 4”级获得的系数，是分类变量的线性，二次和三次趋势。 此处假定分类变量由基本等距的数字变量表示。
# 因此，这种类型的编码仅用于具有相等间隔的有序分类变量。 通常，多项式对比产生阶数为k-1的多项式。 由于“ race”不是
# 有序因子变量，因此我们以 “read” 为例。 首先，我们需要根据 “read” 创建一个有序的分类。


hsb2['readcat'] = np.asarray(pd.cut(hsb2.read, bins=3))
hsb2.groupby('readcat').mean()['write']

from patsy.contrasts import Poly
levels = hsb2.readcat.unique().tolist()
contrast = Poly().code_without_intercept(levels)
print(contrast.matrix)

mod = ols("write ~ C(readcat, Poly)", data=hsb2)
res = mod.fit()
print(res.summary())

# 如您所见，readcat对因变量写有显着的线性影响，但对二次或三次无明显影响。
