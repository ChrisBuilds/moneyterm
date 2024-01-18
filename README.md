<br/>
<p align="center">

  <h3 align="center">MoneyTerm</h3>

  <p align="center">
    TUI Expense and Budget Tracker
    <br/>
    <br/>
  </p>
</p>

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/moneyterm) ![PyPI - Version](https://img.shields.io/pypi/v/moneyterm) 



## Table Of Contents

* [About](#tte)
* [Installation](#installation)
* [Usage](#usage)
* [License](#license)


## MoneyTerm

MoneyTerm is a Textual/Rich TUI based expense and budget tracker with the following features:
* QFX/OFX Importing
* Transaction Table View
* Automatic/Manual Transaction Labeling
* Trend Analysis
* Budget Tracking

## Installation


```pipx install moneyterm```

## Usage

```moneyterm```

MoneyTerm supports importing QFX/OFX files. These are typically available as export options from your bank's online banking website. To import transactions, enter an import directory and file extension in the Config tab. Any files discovered will be automatically imported. Duplicate transactions will be ignored.

#### Transaction Table

Start by selecting an account, year, and month from the scope selection drop downs at the top of the application. The Transactions tab displays an interactive datatable of all transactions for the selected account/year/month. 

![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/74793183-1a45-4432-abaa-fcd465bc40d4)

#### Transaction Details

Use the keyboard shortcut *I* to view transaction details. Transaction details includes all information provided by the banking institution as well as information on any automatic labels, manual labels, and transaction splits. Any manually added labels will be displayed at the bottom of the transaction details window. Click on a label to remove it.

![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/00ef9345-3d2a-49c7-a8f4-1e583e341906)

#### Quick Labeling

Use the keyboard shortcut *c* to quickly add a label to a transaction. A *Quick Label* window will appear. Select a label from the list of available labels, or begin typing a label to filter the list. Press enter to add the label to the transaction. Manually added labels will be displayed at the bottom of the transaction details window. Click on a label to remove it. Manually added labels will be automatically modified/removed corresponding to any changes made to the label in the *Labels* tab.

![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/39ae6ae0-4168-484c-a6d0-2fcec3f8eb4f)

#### Transaction Splitting

Transactions can be split across multiple labels. The total amount across all splits must be less than or equal to the transaction amount. To split a transaction, use the keyboard shortcut */*. A *Split Transaction* window will appear. Enter the amounts for each label. Any amount not accounted for by a split will be ignored by budgets/trends. Labels must be automatically/manually added to the transaction prior to splitting.

![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/65812c0c-3097-45c2-a8a0-9f795eb59305)

#### Automatic Expense Labeling

Labels for Incomes, Bills, and Expenses can be created in the *Labeler* tab. Labels of the type *Incomes* or *Bills* will be shown in the overview tab in tables. *Expense* labels are used in budgeting and trend analysis. Any label created in the *Labeler* tab can be manually applied to a transaction in the *Transactions* tab. Labels can also be automatically applied to transactions based on the *Match Fields* specified for the given label. Matches can be based on date (exact or range), memo/payee fields (exact or substring), amount (exact or range), and/or transaction type (debit/credit/pos/etc). Multiple match filters can be specified for a single label. 

For example: A label for Groceries may have a match for *Kroger* and another match for *Whole Foods*. 

In addition, labels can have an Alias specified. Any transaction matching the label will appear in the Transaction Table with the Payee field replaced by the alias. The *Labeler* has a Transaction Table at the bottom of the window. Use the transaction table to find transactions in need of labeling, test labels using the *Show Matches* button, or import the transaction details directly into the *Match Fields* using the keyboard shortcut *ctrl-l*.

![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/49fca093-a95e-4304-b2e2-a4f94d52eb17)

#### Trend Analysis

Select a label from the *Trends* tab to view a trend analysis for the selected label. The trend analysis will display a bar graph showing the total amount spent on this category, by month, for the selected date range. Additional information is available in a stats table on the left of a given analysis, and each month's total is displayed in an additional table at the bottom of an analysis view. Multiple analysis views can be opened at once.

![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/01c47f4d-ddaf-4af4-89b0-1bc430165d98)

#### Budgeting

Use the *Budget* tab to create budgets for labels. Budgets can be created for any *Expense* label. Specify a monthly budget amount and save the budget to update the budgets table. The budgets table will show the spending for the current month as well as the spending/remaining from the prior month.

![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/55266870-1f20-4fde-945a-5552a4e44a94)

#### Overview (in progress)

The *Overview* tab shows all transactions labeled as a *Bill* or *Income* in separate tables, as well as totals. The overview table can show all relevant transactions in an account, or only the selected year or month. Remove a year/month selection in the scope select dropdowns at the top of the application to widen the scope displayed.

![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/669794a7-ff3e-4d16-b851-2d3e76bd0eb9)



## License

Distributed under the MIT License. See [LICENSE](https://github.com/ChrisBuilds/terminaltexteffects/blob/main/LICENSE.md) for more information.
