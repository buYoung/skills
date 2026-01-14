# Report Template

HTML report output specification using Tailwind CSS.

## File Naming Convention

| Option | Pattern | Example |
|--------|---------|---------|
| Default | `report/scout-report_[service-name]_[YYYY-MM-DD].html` | `report/scout-report_coffee-subscription_2024-01-14.html` |
| Custom | `[user-folder]/[user-filename].html` | User-specified path |

## HTML Structure

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Scout Report - [Service Name]</title>
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
  <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css" />
  <style>
    body { font-family: "Pretendard Variable", sans-serif; }
    @media print {
      .no-print { display: none; }
      body { -webkit-print-color-adjust: exact; }
    }
  </style>
</head>
<body class="bg-gray-50 text-gray-900 antialiased">
  <!-- Header -->
  <!-- Executive Summary -->
  <!-- Opportunity Scorecard -->
  <!-- Market Sizing Section -->
  <!-- Unit Economics Section -->
  <!-- Competitive Analysis Section -->
  <!-- PMF Indicators Section -->
  <!-- Go/No-Go Recommendation -->
  <!-- Footer -->
</body>
</html>
```

## Section Components

### Header

```html
<header class="bg-white border-b border-gray-200 sticky top-0 z-10">
  <div class="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
    <div>
      <div class="flex items-center gap-3">
        <span class="bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded uppercase tracking-wide">Report</span>
        <p class="text-gray-500 text-sm">[Date]</p>
      </div>
      <h1 class="text-2xl font-bold text-gray-900 mt-1">[Service Name]</h1>
      <p class="text-gray-600 text-sm mt-0.5">[One-line description]</p>
    </div>
    <div class="no-print">
      <button onclick="window.print()" class="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
        </svg>
        Print
      </button>
    </div>
  </div>
  <!-- Progress Bar (Optional decoration) -->
  <div class="h-1 w-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
</header>
```

### Executive Summary

```html
<section class="bg-white rounded-xl shadow-sm border border-gray-100 p-8 mb-8 relative overflow-hidden">
  <div class="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
  <h2 class="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    </svg>
    Executive Summary
  </h2>
  <div class="prose prose-blue max-w-none text-gray-600 leading-relaxed">
    <p>[Summary text goes here...]</p>
  </div>
</section>
```

### Opportunity Scorecard

```html
<section class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
  <div class="flex items-center justify-between mb-6">
    <h2 class="text-lg font-semibold text-gray-900">Opportunity Scorecard</h2>
    <div class="flex items-center gap-2">
      <span class="text-sm text-gray-500">Overall Score</span>
      <span class="text-3xl font-bold text-[grade-color]">[Overall Score]</span>
      <span class="px-2 py-1 rounded bg-gray-100 text-gray-700 text-xs font-bold">[Grade Label]</span>
    </div>
  </div>
  
  <div class="grid grid-cols-2 md:grid-cols-5 gap-6">
    <!-- Score Card Item -->
    <div class="group relative">
      <div class="flex justify-between items-end mb-1">
        <p class="text-sm font-medium text-gray-600 group-hover:text-gray-900">[Dimension]</p>
        <p class="text-lg font-bold text-[color]">[Score]</p>
      </div>
      <!-- Progress Bar -->
      <div class="w-full bg-gray-100 rounded-full h-2">
        <div class="bg-[color] h-2 rounded-full transition-all duration-500" style="width: [Score]%"></div>
      </div>
      <p class="text-xs text-gray-400 mt-1">[Grade]</p>
    </div>
  </div>
</section>
```

### Metric Card

```html
<div class="bg-white rounded-lg border border-gray-100 p-5 hover:shadow-md transition-shadow">
  <div class="flex justify-between items-start">
    <div>
      <p class="text-sm font-medium text-gray-500">[Metric Name]</p>
      <p class="text-2xl font-bold text-gray-900 mt-1">[Value]</p>
    </div>
    <!-- Optional Icon or Trend -->
    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[status-bg-color] text-[status-text-color]">
      [Status]
    </span>
  </div>
  <p class="text-xs text-gray-400 mt-2">[Benchmark/Context]</p>
</div>
```

### Section Container

```html
<section class="mb-10">
  <div class="flex items-center mb-4 border-b border-gray-100 pb-2">
    <span class="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-50 text-blue-600 font-bold text-sm mr-3">
      [#]
    </span>
    <h2 class="text-xl font-bold text-gray-800">[Section Title]</h2>
  </div>
  <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
    <!-- Content -->
  </div>
</section>
```

### Data Table

```html
<div class="overflow-hidden rounded-lg border border-gray-200 shadow-sm mt-4">
  <table class="min-w-full divide-y divide-gray-200">
    <thead class="bg-gray-50">
      <tr>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">[Header 1]</th>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">[Header 2]</th>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">[Header 3]</th>
      </tr>
    </thead>
    <tbody class="bg-white divide-y divide-gray-200">
      <tr class="hover:bg-gray-50 transition-colors">
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">[Data 1]</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">[Data 2]</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">[Data 3]</td>
      </tr>
      <!-- More rows... -->
    </tbody>
  </table>
</div>
```

### Go/No-Go Decision

```html
<section class="bg-gradient-to-br from-[decision-color-from] to-[decision-color-to] rounded-xl shadow-lg p-8 text-center text-white relative overflow-hidden">
  <!-- Decorative background pattern -->
  <div class="absolute inset-0 opacity-10 bg-[url('data:image/svg+xml;base64,...')]"></div>
  
  <div class="relative z-10">
    <h2 class="text-xl font-medium text-white/90 mb-2 uppercase tracking-widest text-xs">Final Recommendation</h2>
    <div class="inline-block border-4 border-white/30 rounded-lg px-8 py-4 my-4 backdrop-blur-sm">
      <p class="text-5xl font-black tracking-tight">[GO / NO-GO]</p>
    </div>
    <p class="mt-4 text-lg text-white/90 max-w-2xl mx-auto leading-relaxed">[Rationale summary]</p>
  </div>
</section>
```

### Footer

```html
<footer class="mt-12 py-8 border-t border-gray-200 text-center">
  <p class="text-gray-400 text-sm">Generated by Biz Opportunity Scout</p>
  <p class="text-gray-300 text-xs mt-1">&copy; [YYYY] Biz Opportunity Scout</p>
</footer>
```

## Color Scheme

| Score Range | Background | Text | Progress Color | Usage |
|-------------|------------|------|----------------|-------|
| Excellent (80-100) | `bg-green-50` | `text-green-700` | `bg-green-500` | Strong positive signal |
| Good (60-79) | `bg-blue-50` | `text-blue-700` | `bg-blue-500` | Positive signal |
| Moderate (40-59) | `bg-yellow-50` | `text-yellow-700` | `bg-yellow-500` | Neutral/caution |
| Poor (20-39) | `bg-orange-50` | `text-orange-700` | `bg-orange-500` | Concern |
| Critical (0-19) | `bg-red-50` | `text-red-700` | `bg-red-500` | Major risk |

## Scorecard Dimensions

| Dimension | Weight | Scoring Criteria |
|-----------|--------|------------------|
| Market Size | 20% | TAM/SAM/SOM attractiveness |
| Unit Economics | 25% | LTV:CAC, margins, payback |
| Competition | 20% | Moat potential, entry barriers |
| PMF Signal | 20% | Retention, growth indicators |
| Execution Risk | 15% | Complexity, resource requirements |

## Grade Labels

| Score | Grade | Label |
|-------|-------|-------|
| 90-100 | A+ | Exceptional Opportunity |
| 80-89 | A | Strong Opportunity |
| 70-79 | B+ | Good Opportunity |
| 60-69 | B | Moderate Opportunity |
| 50-59 | C | Marginal Opportunity |
| 40-49 | D | Weak Opportunity |
| < 40 | F | Not Recommended |

## Go/No-Go Logic

| Overall Score | Recommendation | Gradient Classes |
|---------------|----------------|------------------|
| ≥ 70 | GO | `from-green-600 to-emerald-700` |
| 50-69 | CONDITIONAL | `from-yellow-500 to-orange-500` |
| < 50 | NO-GO | `from-red-600 to-rose-700` |
