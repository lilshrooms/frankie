# Criteria Folder

This folder contains YAML files defining underwriting criteria for each loan type.

## How to Use
- Each loan type (e.g., conventional, FHA, jumbo) should have its own YAML file (e.g., `conventional_standard.yaml`).
- These files are loaded by the application to provide context to the AI model when evaluating loan requests.
- To add or update criteria, edit the relevant YAML file.

## Loan Product YAMLs
| File                      | Loan Product                  | Description                                 |
|--------------------------|-------------------------------|---------------------------------------------|
| conventional_standard.yaml| Standard Conventional         | Standard conforming loans (Fannie/Freddie)  |
| homeready.yaml            | HomeReady (Fannie Mae)        | Affordable lending, low down payment        |
| homepossible.yaml         | Home Possible (Freddie Mac)   | Affordable lending, low down payment        |
| high_balance.yaml         | High-Balance/Conforming Jumbo | High-cost area conforming loans             |
| fha.yaml                  | FHA                           | Federal Housing Administration loans        |
| va.yaml                   | VA                            | Veterans Affairs loans                      |
| usda.yaml                 | USDA                          | Rural/USDA guaranteed loans                 |
| jumbo.yaml                | Jumbo                         | Loans above conforming limits               |
| nonqm.yaml                | Non-QM                        | Non-Qualified Mortgage (non-standard)       |

## Example Structure
```
loan_type: conventional_standard
min_credit_score: 620
max_dti: 45
required_documents:
  - pay_stubs
  - bank_statements
  - credit_report
notes:
  - No bankruptcies in last 4 years
  - Stable employment history
```

Each YAML includes references as comments to official Fannie Mae, Freddie Mac, HUD, VA, USDA, or other authoritative documentation. 