// Small reusable behaviours as Stimulus controllers (self-hosted, no build step). Add one class per behaviour.
import {Application, Controller} from '/static/vendor/stimulus/stimulus.js';

class ToastController extends Controller {
  connect() {
    this.onNotice = event => this.show(event.detail);
    this.element.addEventListener('site:notice', this.onNotice);
  }
  disconnect() {
    clearTimeout(this.timer);
    this.element.removeEventListener('site:notice', this.onNotice);
  }
  show({message, error = false}) {
    clearTimeout(this.timer);
    this.element.textContent = message;
    this.element.classList.toggle('error', error);
    if (message) this.timer = setTimeout(() => { this.element.textContent = ''; }, error ? 8000 : 4000);
  }
}

const application = Application.start();
application.register('toast', ToastController);
const notice = document.getElementById('notice');
if (notice) notice.dataset.controller = 'toast';
