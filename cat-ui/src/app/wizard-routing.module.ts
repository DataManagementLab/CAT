import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';
import {HomeComponent} from './components/home/home.component';
import {ConfigurationStepperComponent} from './components/configuration/configuration-stepper.component';
import {TrainingStepperComponent} from './components/training/training-stepper.component';

const routes: Routes = [
  {path: '', component: HomeComponent},
  {path: 'configuration', component: ConfigurationStepperComponent},
  {path: 'training', component: TrainingStepperComponent},
];

@NgModule({
  declarations: [],
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class WizardRoutingModule {
}
