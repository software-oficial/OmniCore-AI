/**
 * 🚀 Master Dock Loader
 * Carga secuencialmente las dependencias de la UI para garantizar
 * que el Dock se inicialice correctamente sin conflictos de carga.
 */
(function() {
  const scripts = [
    '/js/icons.js',
    '/js/apply_icons.js',
    '/js/dock.js'
  ];

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  async function init() {
    // Añadir contenedor de toasts si no existe
    if (!document.getElementById('toast-container')) {
        const toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'fixed top-5 right-5 z-[100] flex flex-col gap-3';
        document.body.appendChild(toastContainer);
    }

    for (const src of scripts) {
      try {
        await loadScript(src);
      } catch (e) {
        console.error('Error cargando dependencia:', src, e);
      }
    }
  }

  init();
})();
