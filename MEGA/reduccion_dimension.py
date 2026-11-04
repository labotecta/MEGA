from scipy.stats import f
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import pandas
from matplotlib import pyplot as plt
import seaborn as sns
import MEGA as prin

def reduce(SENDA_GRAFICOS, nombre, X, y, nd=2, semilla=42):
    tsne = TSNE(n_components=nd, perplexity=30, random_state=42)
    X_tsne = tsne.fit_transform(X)
    fig = plt.figure(figsize=(10, 7))
    scatter = plt.scatter(X_tsne[:, 0], X_tsne[:, 1], c=y, cmap='viridis', edgecolor='k', s=50)
    plt.xlabel('Primer Componente')
    plt.ylabel('Segundo Componente')
    plt.title('Reducción de dimensionalidad con TSNE')
    plt.colorbar(scatter, label='demerito relativo')
    plt.grid(True)
    plt.savefig(SENDA_GRAFICOS + nombre + 'TSNE.png', dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
    plt.close()

    pca = PCA(n_components=nd)
    X_pca = pca.fit_transform(X)
    fig = plt.figure(figsize=(10, 7))
    scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=y, cmap='viridis', edgecolor='k', s=50)
    plt.xlabel('Primer Componente Principal')
    plt.ylabel('Segundo Componente Principal')
    plt.title('Reducción de dimensionalidad con PCA')
    plt.colorbar(scatter, label='demerito relativo')
    plt.grid(True)
    plt.savefig(SENDA_GRAFICOS + nombre + 'PCA.png', dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
    plt.close()

    nc = X.shape[1]
    pca0 = pca.components_[0, :] 
    pca1 = pca.components_[1, :] 
    prin.imprime('')
    for k in range(2):
        cpnte = pca.components_[k, :] 
        prin.imprime('Componente PCA({:1d})'.format(k + 1))
        cc = -1;
        for i in range(nc):
            cc += 1
            if cc % 10 == 0:
                prin.imprime('')
            prin.imprime('{:10.3f} '.format(cpnte[i]), False)
        prin.imprime('')
    prin.imprime('')

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    merito_df = pandas.DataFrame(X_scaled)
    merito_df['demerito'] = y
    tsne = TSNE(n_components=2, perplexity=30, learning_rate=200, random_state=42)
    X_tsne = tsne.fit_transform(X_scaled)
    tsne_df = pandas.DataFrame(data=X_tsne, columns=['TSNE1', 'TSNE2'])
    tsne_df['demerito'] = y
    fig = plt.figure(figsize=(10, 7))
    sns.scatterplot(
        x='TSNE1', 
        y='TSNE2', 
        hue='demerito', 
        palette='deep', 
        data=tsne_df,
        legend='full',
        alpha=0.8
    )
    plt.title('TSNE normalizado')
    plt.xlabel('Componente 1')
    plt.ylabel('Componente 2')
    plt.savefig(SENDA_GRAFICOS + nombre + 'TSNEb.png', dpi = 300, facecolor = 'w', edgecolor = 'w', orientation = 'portrait', format = 'png', transparent = False, bbox_inches = None, pad_inches = 0.1, metadata = None)
    plt.close()
