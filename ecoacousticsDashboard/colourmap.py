import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# Define your color list
colors = ["#6e40aa","#6d41ab","#6d41ad","#6d42ae","#6c43af","#6c43b0","#6b44b2","#6b45b3",
          "#6a46b4","#6a46b5","#6a47b7","#6948b8","#6849b9","#684aba","#674abb","#674bbd",
          "#664cbe","#664dbf","#654ec0","#654fc1","#6450c2","#6350c3","#6351c4","#6252c5",
          "#6153c6","#6154c7","#6055c8","#5f56c9","#5f57ca","#5e58cb","#5d59cc","#5c5acd",
          "#5c5bce","#5b5ccf","#5a5dd0","#595ed1","#595fd1","#5860d2","#5761d3","#5662d4",
          "#5663d5","#5564d5","#5465d6","#5366d7","#5267d7","#5168d8","#5169d9","#506ad9",
          "#4f6bda","#4e6cda","#4d6ddb","#4c6edb","#4b70dc","#4b71dc","#4a72dd","#4973dd",
          "#4874de","#4775de","#4676df","#4577df","#4479df","#447adf","#437be0","#427ce0",
          "#417de0","#407ee0","#3f80e1","#3e81e1","#3d82e1","#3d83e1","#3c84e1","#3b86e1",
          "#3a87e1","#3988e1","#3889e1","#378ae1","#378ce1","#368de1","#358ee1","#348fe1",
          "#3390e1","#3292e1","#3293e1","#3194e0","#3095e0","#2f96e0","#2e98e0","#2e99df",
          "#2d9adf","#2c9bdf","#2b9cde","#2b9ede","#2a9fdd","#29a0dd","#29a1dd","#28a2dc",
          "#27a4dc","#26a5db","#26a6db","#25a7da","#25a8d9","#24aad9","#23abd8","#23acd8",
          "#22add7","#22aed6","#21afd5","#21b1d5","#20b2d4","#20b3d3","#1fb4d2","#1fb5d2",
          "#1eb6d1","#1eb8d0","#1db9cf","#1dbace","#1dbbcd","#1cbccc","#1cbdcc","#1cbecb",
          "#1bbfca","#1bc0c9","#1bc2c8","#1ac3c7","#1ac4c6","#1ac5c5","#1ac6c4","#1ac7c2",
          "#1ac8c1","#19c9c0","#19cabf","#19cbbe","#19ccbd","#19cdbc","#19cebb","#19cfb9",
          "#19d0b8","#19d1b7","#19d2b6","#19d3b5","#1ad4b4","#1ad5b2","#1ad5b1","#1ad6b0",
          "#1ad7af","#1bd8ad","#1bd9ac","#1bdaab","#1bdbaa","#1cdba8","#1cdca7","#1cdda6",
          "#1ddea4","#1ddfa3","#1edfa2","#1ee0a0","#1fe19f","#1fe29e","#20e29d","#20e39b",
          "#21e49a","#22e599","#22e597","#23e696","#24e795","#24e793","#25e892","#26e891",
          "#27e98f","#27ea8e","#28ea8d","#29eb8c","#2aeb8a","#2bec89","#2cec88","#2ded87",
          "#2eed85","#2fee84","#30ee83","#31ef82","#32ef80","#33f07f","#34f07e","#35f07d",
          "#37f17c","#38f17a","#39f279","#3af278","#3bf277","#3df376","#3ef375","#3ff374",
          "#41f373","#42f471","#43f470","#45f46f","#46f46e","#48f56d","#49f56c","#4bf56b",
          "#4cf56a","#4ef56a","#4ff669","#51f668","#52f667","#54f666","#55f665","#57f664",
          "#59f664","#5af663","#5cf662","#5ef661","#5ff761","#61f760","#63f75f","#64f75f",
          "#66f75e","#68f75d","#6af75d","#6bf65c","#6df65c","#6ff65b","#71f65b","#73f65a",
          "#74f65a","#76f659","#78f659","#7af659","#7cf658","#7ef658","#80f558","#81f558",
          "#83f557","#85f557","#87f557","#89f557","#8bf457","#8df457","#8ff457","#91f457",
          "#93f457","#94f357","#96f357","#98f357","#9af357","#9cf257","#9ef258","#a0f258",
          "#a2f258","#a4f158","#a6f159","#a8f159","#aaf159","#abf05a","#adf05a","#aff05b"]

# Create the colormap
cmap = mcolors.ListedColormap(colors)

# Display it as a colorbar
fig, ax = plt.subplots(figsize=(8, 1))
fig.subplots_adjust(bottom=0.5)

# Create a scalar mappable and colorbar
norm = mcolors.BoundaryNorm(boundaries=np.arange(len(colors)+1), ncolors=len(colors))
cb = plt.colorbar(mappable=plt.cm.ScalarMappable(norm=norm, cmap=cmap),
                  cax=ax, orientation='horizontal', ticks=[])
cb.set_label('Discrete Colormap with {} Colors'.format(len(colors)))

plt.show()

