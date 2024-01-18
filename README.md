<br/>
<p align="center">

  <h3 align="center">MoneyTerm</h3>

  <p align="center">
    TUI Expense and Budget Tracker
    <br/>
    <br/>
  </p>
</p>

## Table Of Contents

* [About](#tte)
* [Installation](#installation)
* [Screenshots](#screenshots)
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


## Screenshots
#### Transaction Table

Start by selecting an account, year, and month from the scope selection drop downs at the top of the application. The Transactions tab displays an interactive datatable of all transactions for the selected account/year/month. 

![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/74793183-1a45-4432-abaa-fcd465bc40d4)

#### Transaction Details

Use the keyboard shortcut *I* to view transaction details. Transaction details includes all information provided by the banking institution as well as information on any automatic labels, manual labels, and transaction splits. Any manually added labels will be displayed at the bottom of the transaction details window. Click on a label to remove it.

![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/00ef9345-3d2a-49c7-a8f4-1e583e341906)

#### Quick Labeling

Use the keyboard shortcut *c* to quickly add a label to a transaction. A *Quick Label* window will appear. Select a label from the list of available labels, or begin typing a label to filter the list. Press enter to add the label to the transaction. Manually added labels will be displayed at the bottom of the transaction details window. Click on a label to remove it. Manually added labels will be automatically modified/removed corresponding to any changed made to the label in the *Labels* tab.

![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/39ae6ae0-4168-484c-a6d0-2fcec3f8eb4f)

#### Transaction Splitting
![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/65812c0c-3097-45c2-a8a0-9f795eb59305)

#### Automatic Expense Labeling
![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/49fca093-a95e-4304-b2e2-a4f94d52eb17)

#### Trend Analysis
![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/01c47f4d-ddaf-4af4-89b0-1bc430165d98)

#### Budgeting
![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/55266870-1f20-4fde-945a-5552a4e44a94)

#### Overview (in progress)
![image](https://github.com/ChrisBuilds/moneyterm/assets/57874186/669794a7-ff3e-4d16-b851-2d3e76bd0eb9)



## License

Distributed under the MIT License. See [LICENSE](https://github.com/ChrisBuilds/terminaltexteffects/blob/main/LICENSE.md) for more information.
