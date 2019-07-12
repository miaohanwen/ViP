import os
import sys 
import datetime
import yaml 
import torch

import numpy             as np
import torch.nn          as nn
import torch.optim       as optim

from torch.optim.lr_scheduler           import MultiStepLR
from tensorboardX                       import SummaryWriter

from parse_args                         import Parse
from models.models_import               import create_model_object
from datasets                           import data_loader 
from losses                             import Losses
from metrics                            import Metrics
from checkpoint                         import save_checkpoint, load_checkpoint

def train(**args):

    print("\n############################################################################\n")
    print("Experimental Setup: ", args)
    print("\n############################################################################\n")

    for total_iteration in range(args['rerun']):

        # Generate Results Directory
        d          = datetime.datetime.today()
        date       = d.strftime('%Y%m%d-%H%M%S')
        result_dir = os.path.join(args['save_dir'], args['model'], '_'.join((args['dataset'],args['exp'],date)))
        log_dir    = os.path.join(result_dir,       'logs')
        save_dir   = os.path.join(result_dir,       'checkpoints')

        if not args['debug']:
            os.makedirs(result_dir, exist_ok=True)
            os.makedirs(log_dir,    exist_ok=True) 
            os.makedirs(save_dir,   exist_ok=True) 

            # Save Copy of Config File
            with open(os.path.join(result_dir, 'config.yaml'),'w') as outfile:
                yaml.dump(args, outfile, default_flow_style=False)


            # Tensorboard Element
            writer = SummaryWriter(log_dir)

        # Load Data
        loader = data_loader(**args)

        if args['load_type'] == 'train':
            train_loader = loader['train']
            valid_loader = loader['train'] # Run accuracy on train data if only `train` selected

        elif args['load_type'] == 'train_val':
            train_loader = loader['train']
            valid_loader = loader['valid'] 

        else:
            sys.exit('Invalid environment selection for training, exiting')

        # END IF
    
        # Check if GPU is available (CUDA)
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    
        # Load Network
        model = create_model_object(**args).to(device)

        if isinstance(args['pretrained'], str):
            ckpt = load_checkpoint(args['pretrained'])
            model.load_state_dict(ckpt)


        # Training Setup
        params     = [p for p in model.parameters() if p.requires_grad]

        if args['opt'] == 'sgd':
            optimizer  = optim.SGD(params, lr=args['lr'], momentum=args['momentum'], weight_decay=args['weight_decay'])

        elif args['opt'] == 'adam':
            optimizer  = optim.Adam(params, lr=args['lr'], weight_decay=args['weight_decay'])
        
        else:
            sys.exit('Unsupported optimizer selected. Exiting')

        # END IF
            
        scheduler  = MultiStepLR(optimizer, milestones=args['milestones'], gamma=args['gamma'])    
        model_loss = Losses(device=device, **args)
        #acc_metric = Metrics(**args)

    ############################################################################################################################################################################


        # Start: Training Loop
        for epoch in range(args['epoch']):
            running_loss = 0.0
            print('Epoch: ', epoch)

            # Setup Model To Train 
            model.train()

            # Start: Epoch
            for step, data in enumerate(train_loader):

<<<<<<< HEAD:train_recognition.py
                # (True Batch, Augmented Batch, Sequence Length)
                #data = dict((k, v.to(device)) for k,v in data.items())
                # Self-supervised
                #x_input       = data['data']
                #import pdb; pdb.set_trace()
                #x_input1       = x_input.view(args['batch_size']*4, 3, args['sample_duration'], args['final_shape'][0], args['final_shape'][1])
=======
>>>>>>> 5f37cbaab4e1a8f71132931cb962cc1bf1e2866c:train.py
                x_input       = data['data'].to(device) 
                annotations   = data['annots'] 

                optimizer.zero_grad()

                outputs = model(x_input)
                loss    = model_loss.loss(outputs.to('cpu'), annotations)
    
                loss.backward()
                optimizer.step()
    
                running_loss += loss.item()

                if not args['debug']:
                    # Add Learning Rate Element
                    for param_group in optimizer.param_groups:
                        writer.add_scalar(args['dataset']+'/'+args['model']+'/learning_rate', param_group['lr'], epoch*len(train_loader) + step)
                
                        # Add Loss Element
                        writer.add_scalar(args['dataset']+'/'+args['model']+'/minibatch_loss', loss.item(), epoch*len(train_loader) + step)

                if np.isnan(running_loss):
                    import pdb; pdb.set_trace()

                if ((epoch*len(train_loader) + step+1) % 100 == 0):
                    print('Epoch: {}/{}, step: {}/{} | train loss: {:.4f}'.format(epoch, args['epoch'], step+1, len(train_loader), running_loss/float(step+1)))

                # END IF

            if not args['debug']:
                # Save Current Model
                save_path = os.path.join(save_dir, args['dataset']+'_epoch'+str(epoch)+'.pkl')
                save_checkpoint(epoch, step, model, optimizer, save_path)
   
            # END FOR: Epoch

            scheduler.step()

            ## START FOR: Validation Accuracy
            #model.eval()

            #running_acc = []
            #running_acc = valid(valid_loader, running_acc, writer, model, device, acc_metric)
            #
            #writer.add_scalar(args['dataset']+'/'+args['model']+'/validation_accuracy', 100.*running_acc[-1], epoch*len(train_loader) + step)
            #print('Accuracy of the network on the validation set: %f %%\n' % (100.*running_acc[-1]))

        # END FOR: Training Loop

    ############################################################################################################################################################################

        if not args['debug']:
            # Close Tensorboard Element
            writer.close()

def valid(valid_loader, running_acc, writer, model, device, acc_metric):
    model.eval()
    
    for step, data in enumerate(valid_loader):
        x_input = data['data'].to(device)
        y_label = data['labels'] 
        outputs = model(x_input)
    
        running_acc.append(acc_metric.get_accuracy(outputs.detach().cpu().numpy(), y_label.numpy()))
    
    # END FOR: Validation Accuracy

    return running_acc


if __name__ == "__main__":

    parse = Parse()
    args = parse.get_args()

    # For reproducibility
    torch.backends.cudnn.deterministic = True
    torch.manual_seed(args['seed'])
    np.random.seed(args['seed'])

    train(**args)