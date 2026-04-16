import matplotlib.pyplot as plt
import numpy as np

laps = np.arange(1, 16)
errors = [0.1716, 0.1560, 0.1537, 0.1378, 0.1358, 0.1219, 0.1202,
          0.1081, 0.1068, 0.0961, 0.0951, 0.0860, 0.0851, 0.0770, 0.0763]
taup_vals = [0.40, 0.45, 0.5050, 0.5050, 0.5655, 0.5655, 0.6321,
             0.6321, 0.7053, 0.7053, 0.7858, 0.7858, 0.8744, 0.8744, 0.9718]
taud_vals = [0.60, 0.65, 0.65, 0.7050, 0.7050, 0.7655, 0.7655,
             0.8321, 0.8321, 0.9053, 0.9053, 0.9858, 0.9858, 1.0744, 1.0744]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
fig.suptitle('Twiddle Optimization: Error and Parameter Evolution',
             fontsize=14, fontweight='bold')

ax1.plot(laps, errors, marker='o', color='#d62728',
         linewidth=2, label='Average CTE')
for i, txt in enumerate(errors):
    ax1.annotate(f'{txt:.3f}',
                 (laps[i], errors[i]),
                 textcoords="offset points",
                 xytext=(0, 8),
                 ha='center',
                 fontsize=9)
ax1.set_ylabel('Average Error (|cte|)', fontsize=12)
ax1.grid(True, linestyle='--', alpha=0.7)
ax1.legend(loc='upper right')
ax1.set_title('Cross-Track Error Minimization', fontsize=12)

ax2.plot(laps, taup_vals, marker='s', color='#1f77b4',
         linewidth=2, label='Proportional Gain ($\\tau_p$)')
ax2.plot(laps, taud_vals, marker='^', color='#2ca02c',
         linewidth=2, label='Derivative Gain ($\\tau_d$)')
for i, txt in enumerate(taup_vals):
    ax2.annotate(f'{txt:.2f}',
                 (laps[i], taup_vals[i]),
                 textcoords="offset points",
                 xytext=(0, -15),
                 ha='center',
                 fontsize=9,
                 color='#1f77b4')

for i, txt in enumerate(taud_vals):
    ax2.annotate(f'{txt:.2f}',
                 (laps[i], taud_vals[i]),
                 textcoords="offset points",
                 xytext=(0, 8),
                 ha='center',
                 fontsize=9,
                 color='#2ca02c')
ax2.set_xlabel('Lap Number', fontsize=12)
ax2.set_ylabel('Gain Value', fontsize=12)
ax2.grid(True, linestyle='--', alpha=0.7)
ax2.legend(loc='upper left')
ax2.set_title('Parameter Space Search ($\\tau_p$, $\\tau_d$)', fontsize=12)

plt.xticks(laps)
plt.tight_layout()
plt.subplots_adjust(top=0.92)

plt.savefig('img/twiddle_results.png', dpi=300, bbox_inches='tight')
