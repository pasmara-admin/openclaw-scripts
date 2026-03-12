
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Data (Year to Date 2026)
data = {
    'Shop': ['ProduceShop IT', 'ProduceShop FR', 'ProduceShop DE', 'ProduceShop ES', 'ProduceShop AT'],
    'Revenue (€)': [778159.17, 249503.29, 187928.65, 106104.16, 76800.65],
    'Orders': [3916, 1072, 1026, 545, 374]
}

df = pd.DataFrame(data)

# Sort by Revenue for better visualization
df = df.sort_values('Revenue (€)', ascending=True)

# Plotting
fig, ax1 = plt.subplots(figsize=(12, 8))

# Bar chart for Revenue
sns.set_theme(style="whitegrid")
bars = ax1.barh(df['Shop'], df['Revenue (€)'], color='skyblue', label='Fatturato (Revenue)')

# Add value labels for Revenue
for bar in bars:
    width = bar.get_width()
    ax1.text(width, bar.get_y() + bar.get_height()/2, 
             f'€{width:,.0f}', 
             va='center', ha='left', fontsize=10, fontweight='bold', color='black')

# Secondary axis for Orders (optional, but let's keep it simple and just annotate)
# Instead of a secondary axis which can be confusing on barh, let's add the order count to the y-axis label
new_labels = [f"{row.Shop}\n({row.Orders} orders)" for index, row in df.iterrows()]
ax1.set_yticklabels(new_labels)

ax1.set_xlabel('Fatturato Totale 2026 (YTD) - €', fontsize=12)
ax1.set_title('Confronto Performance Shop (2026 Year-to-Date)', fontsize=16)
ax1.grid(axis='x', linestyle='--', alpha=0.7)

# Adjust layout to make room for labels
plt.tight_layout()

# Save
plt.savefig('shops_comparison_2026.png')
print("Chart generated: shops_comparison_2026.png")
