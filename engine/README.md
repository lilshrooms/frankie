# Rate Optimizer Engine

The Rate Optimizer Engine is a comprehensive system that analyzes mortgage loan scenarios and suggests optimizations to reduce rates, fees, and total interest costs. It integrates with the rate ingestion system and can optionally use Gemini AI for enhanced analysis.

## Features

### Core Optimization Engine
- **Credit Score Optimization**: Suggests improvements to credit scores with rate savings and timeframes
- **LTV Optimization**: Analyzes down payment increases with ROI calculations
- **Loan Amount Optimization**: Shows savings from reducing loan amounts
- **Loan Type Optimization**: Compares different loan types for better rates
- **Feasibility Assessment**: Evaluates how realistic each optimization is
- **ROI Analysis**: Calculates return on investment for down payment increases

### Rate Quote Analyzer
- **Human-Readable Explanations**: Clear, conversational explanations of why borrowers got their specific rate
- **Rate Breakdown Analysis**: Detailed explanation of rate components (base rate, LLPAs, adjustments)
- **Improvement Suggestions**: 1-2 actionable ways to improve the rate
- **Market Context**: Current market conditions and timing insights
- **Gemini AI Integration**: Enhanced analysis using Google's Gemini AI

### AI Integration
- **Gemini AI Analysis**: Enhanced insights using current market data
- **Priority Recommendations**: AI-ranked optimization suggestions
- **Market Context**: Incorporates current rate trends and market conditions
- **Borrower-Specific Advice**: Tailored recommendations based on profile
- **Next Steps**: Actionable implementation guidance

### API Interface
- **REST API**: FastAPI-based endpoints for integration
- **Quick Optimization**: Simple query parameter interface
- **Comprehensive Analysis**: Full optimization results with AI insights
- **Input Validation**: Robust parameter validation and error handling

## Quick Start

### Basic Usage

```python
from optimizer import optimize_scenario

# Analyze a loan scenario
result = optimize_scenario(
    loan_amount=500000,
    credit_score=680,
    ltv=85,
    loan_type="30yr_fixed"
)

# Get optimization results
if not result.get('error'):
    current = result['current_scenario']
    summary = result['summary']
    
    print(f"Current Rate: {current['final_rate']}%")
    print(f"Total Potential Savings: ${summary['total_potential_savings']:,.2f}")
    
    for rec in summary['recommendations']:
        print(f"- {rec}")
```

### AI-Enhanced Analysis

```python
from gemini_optimizer_integration import analyze_optimization_with_ai

# Get AI-enhanced analysis
result = analyze_optimization_with_ai(
    loan_amount=500000,
    credit_score=680,
    ltv=85
)

# Access AI insights
if result.get('ai_analysis', {}).get('success'):
    ai_insights = result['ai_analysis']['insights']
    print("AI Priority Recommendations:")
    for rec in ai_insights['priority_recommendations']:
        print(f"- {rec}")
```

### Generate Reports

```python
from gemini_optimizer_integration import generate_optimization_report

# Generate comprehensive report
report = generate_optimization_report(
    loan_amount=500000,
    credit_score=680,
    ltv=85
)
print(report)
```

### Analyze Rate Quotes

```python
from analyzer import analyze_quote, generate_quote_summary
from quote_engine import quote_rate

# Get a quote
quote_result = quote_rate(500000, 680, 85, "30yr_fixed", current_rates)

# Create borrower profile
borrower_profile = {
    "loan_amount": 500000,
    "credit_score": 680,
    "ltv": 85,
    "loan_type": "30yr_fixed",
    "property_type": "Primary Residence",
    "occupancy": "Owner Occupied"
}

# Analyze the quote
analysis = analyze_quote(quote_result, borrower_profile)

# Get explanation and suggestions
print(f"Explanation: {analysis['explanation']}")
for suggestion in analysis['improvement_suggestions']:
    print(f"- {suggestion['suggestion']}")

# Generate formatted summary
summary = generate_quote_summary(quote_result, borrower_profile)
print(summary)
```

## API Usage

### Start the API Server

```bash
cd engine
python optimizer_api.py
```

The API will be available at `http://localhost:8001`

### API Endpoints

#### POST /optimize
Full optimization analysis with detailed results.

```bash
curl -X POST "http://localhost:8001/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_amount": 500000,
    "credit_score": 680,
    "ltv": 85,
    "loan_type": "30yr_fixed"
  }'
```

#### GET /optimize/quick
Quick optimization summary with query parameters.

```bash
curl "http://localhost:8001/optimize/quick?loan_amount=500000&credit_score=680&ltv=85"
```

### Rate Analyzer API

#### POST /analyze
Analyze a rate quote with Gemini AI.

```bash
curl -X POST "http://localhost:8002/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "quote_result": {...},
    "borrower_profile": {...}
  }'
```

#### GET /analyze/quick
Quick analysis with automatic quote generation.

```bash
curl "http://localhost:8002/analyze/quick?loan_amount=500000&credit_score=680&ltv=85"
```

## Optimization Types

### 1. Credit Score Optimization
- **Targets**: 680 (Good), 720 (Excellent), 760 (Premium)
- **Analysis**: Rate savings, monthly savings, total interest savings
- **Feasibility**: Based on improvement needed (high/medium/low)
- **Timeframe**: Estimated time to achieve target score

### 2. LTV Optimization
- **Targets**: 80% (Conventional), 70% (Better rates), 60% (Premium)
- **Analysis**: Rate savings, additional down payment needed
- **ROI**: Return on investment for additional down payment
- **Payback Period**: Years to recoup additional down payment

### 3. Loan Amount Optimization
- **Scenarios**: 5%, 10%, 15% reductions
- **Analysis**: Monthly savings, total interest savings
- **Feasibility**: Based on reduction percentage
- **Impact**: Moderate or significant

### 4. Loan Type Optimization
- **Alternatives**: 15yr_fixed, FHA, VA, Jumbo, ARMs
- **Analysis**: Rate comparison, payment differences
- **Considerations**: Requirements, risks, benefits
- **Feasibility**: Based on borrower eligibility

## Output Structure

### Optimization Result
```json
{
  "current_scenario": {
    "final_rate": 5.938,
    "monthly_payment": 2977.69,
    "total_interest": 571968.40
  },
  "credit_score_optimizations": [...],
  "ltv_optimizations": [...],
  "loan_amount_optimizations": [...],
  "loan_type_optimizations": [...],
  "summary": {
    "total_potential_savings": 86169.60,
    "recommendations": [...],
    "quick_wins": [...],
    "long_term_improvements": [...]
  }
}
```

### AI Analysis
```json
{
  "ai_analysis": {
    "success": true,
    "insights": {
      "priority_recommendations": [...],
      "market_insights": "...",
      "borrower_advice": "...",
      "financial_impact": "...",
      "next_steps": [...]
    }
  }
}
```

## Configuration

### Rate Data
The optimizer uses current rates from the rate ingestion system:
- Automatically fetches latest rates
- Supports multiple loan types
- Includes LLPAs and adjustments

### AI Integration
- Requires Google Gemini API key
- Optional enhancement (works without AI)
- Configurable analysis depth

### LLPAs (Loan Level Price Adjustments)
- Credit score adjustments: +0.125% for <680
- LTV adjustments: +0.25% for >80%
- Configurable in quote engine

## Testing

### Run Basic Tests
```bash
cd engine
python optimizer.py
python test_optimizer.py
```

### Run AI Integration Tests
```bash
python gemini_optimizer_integration.py
```

### Test API
```bash
python optimizer_api.py
# Then visit http://localhost:8001/docs for interactive API docs
```

### Test Analyzer
```bash
python analyzer.py
python test_analyzer_with_api.py
```

## Integration with Frankie Platform

### Email Pipeline Integration
The optimizer can be integrated into the email analysis pipeline:

```python
from optimizer import optimize_scenario

# In email analysis
if loan_info:
    optimization = optimize_scenario(
        loan_info['amount'],
        loan_info['credit_score'],
        loan_info['ltv']
    )
    
    # Include optimization in email response
    response += f"\n\nRate Optimization Suggestions:\n"
    for rec in optimization['summary']['recommendations'][:2]:
        response += f"• {rec}\n"
```

### Dashboard Integration
The API can be called from the frontend dashboard:

```javascript
// Frontend API call
const response = await fetch('/api/optimize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    loan_amount: 500000,
    credit_score: 680,
    ltv: 85
  })
});

const result = await response.json();
// Display optimization results in UI
```

## Dependencies

- `quote_engine.py`: Core quoting functionality
- `rate_scheduler.py`: Rate data management
- `gemini_rate_integration.py`: AI integration
- `analyzer.py`: Rate quote analysis with Gemini AI
- FastAPI: API framework
- Google Generative AI: AI analysis

## Future Enhancements

1. **Historical Analysis**: Compare optimizations over time
2. **Scenario Modeling**: What-if analysis for different scenarios
3. **Market Timing**: Optimal timing recommendations
4. **Refinance Analysis**: Compare current vs. new loan scenarios
5. **Portfolio Optimization**: Multi-property analysis
6. **Risk Assessment**: Include risk factors in recommendations

## Troubleshooting

### Common Issues

1. **No rates available**: Run rate scheduler to collect current rates
2. **AI analysis fails**: Check Gemini API key configuration
3. **Import errors**: Ensure all dependencies are installed
4. **Calculation errors**: Verify input parameters are within valid ranges

### Debug Mode
Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Ensure backward compatibility
5. Test with real rate data

## License

Part of the Frankie B2B AI-powered loan assistant platform. 