from __future__ import division
import torch
import torch.nn as nn
import torchvision.datasets as datasets
import torchvision.transforms as transforms
from torch.autograd import Variable
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import time
#import cv2
import os

kwargs = {'num_workers': 1, 'pin_memory': True}
train_loader = torch.utils.data.DataLoader(
    datasets.MNIST('../tmp', train=True, download=True,
                   transform=transforms.Compose([
                       transforms.ToTensor(),
                   ])),
    batch_size=1024, shuffle=True, **kwargs)
test_loader = torch.utils.data.DataLoader(
    datasets.MNIST('../tmp', train=False, transform=transforms.Compose([
                       transforms.ToTensor(),
                   ])),
    batch_size=400, shuffle=False, **kwargs)

I_n=30
model_pth='./model/ori_sourec_m_'+str(I_n)+'.pkl'

class classifier(nn.Module):
    def __init__(self):
        super(classifier, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv3 = nn.Conv2d(20, 10, kernel_size=4)
        self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)
        self.norm1 = nn.BatchNorm2d(1)
        self.norm2 = nn.BatchNorm2d(10)
        self.norm3 = nn.BatchNorm2d(20)
        self.norm4 = nn.BatchNorm1d(320)
        self.norm5 = nn.BatchNorm1d(50)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(self.norm1(x)), 2))
        # print (x.size())
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(self.norm2(x))), 2))
        x=x.view(-1, 320)
        x=self.fc1(self.norm4(x))
        x=self.fc2(self.norm5(x))
        return F.log_softmax(x)

class source_m(nn.Module):
    def __init__(self):
        super(source_m, self).__init__()
        self.con1 = nn.Conv2d(1, 20, 5)
        self.con2 = nn.Conv2d(20, 10, 5)
        self.con3=nn.Conv2d(10,20,5)
        self.con4=nn.Conv2d(20,32,5)
        self.fc1 = nn.Linear(4608, 2304)
        self.fc2 = nn.Linear(2304, 4608)

        self.recon1 = nn.ConvTranspose2d(32, 20, 5)
        self.recon2 = nn.ConvTranspose2d(20, 10, 5)
        self.recon3=nn.ConvTranspose2d(10,20,5)
        self.recon4=nn.ConvTranspose2d(20,1, 5)

    def forward(self, x):
        x = self.con1(x)
        x = self.con2(x)
        x=self.con3(x)
        x=self.con4(x)
        #print (x.size())
        x = x.view(-1, 4608)
        x = self.fc1(x)
        x = self.fc2(x)
        #print (x.size())
        x = x.view(-1, 32, 12, 12)
        x = self.recon1(x)
        x = self.recon2(x)
        x=self.recon3(x)
        x=self.recon4(x)
        #print(x.size())
        return x
s_m=source_m()
clas=classifier()
class sour_cls(nn.Module):
    def __init__(self):
        super(sour_cls, self).__init__()
        self.source_m=s_m
        self.classifier=clas
    def forward(self, x):
        x0=self.source_m(x)
        x=self.classifier(x0)
        return x0, x

class fc(nn.Module):
    def __init__(self):
        super(fc, self).__init__()
        self.fc1=nn.Linear(784, 256)
        self.fc2=nn.Linear(256, 10)
    def forward(self, x):
        x=x.view(-1,784)
        x=self.fc1(x)
        x=self.fc2(x)
        return F.log_softmax(x), F.s

def test_train(epoch):

    n=0
    n_loss=0
    for batch_idx, (data, target) in enumerate(test_loader):
        print ('This is {}_epoch: {}_th batch'.format(epoch, batch_idx))
        data, target= Variable(data, requires_grad=True).cuda(), Variable(target).cuda()
        data = Variable(data.data, requires_grad=True)
        '''
        if batch_idx%10==0:#show the img generated by source_m
            tmp_img=model.source_m(data)
            tmp_img=tmp_img.cpu().data.numpy()[0]
            tmp_img=np.reshape(tmp_img, (28,28))
            cv2.imshow('kk', tmp_img)
            cv2.waitKey(200)
            cv2.destroyAllWindows()
        '''

        x0, output=model(data)
        loss=F.nll_loss(output, target)
        pred = output.data.max(1)[1]  # get the index of the max log-probability
        n += pred.eq(target.data).cpu().sum()
        optimizer.zero_grad()
        loss.backward()
        #print (data.grad)
        optimizer.step()


    print ('Train accuracy is {}'.format(n / len(test_loader.dataset)))
    return n / len(test_loader.dataset)


def test_loss(epoch):
    n = 0
    for batch_idx, (data, target) in enumerate(test_loader):
        print ('Loss this is {}_epoch: {}_th batch'.format(epoch, batch_idx))
        data, target = Variable(data, requires_grad=True).cuda(), Variable(target).cuda()
        data = Variable(data.data, requires_grad=True)
        '''
        if batch_idx%10==0:#show the img generated by source_m
            tmp_img=model.source_m(data)
            tmp_img=tmp_img.cpu().data.numpy()[0]
            tmp_img=np.reshape(tmp_img, (28,28))
            cv2.imshow('kk', tmp_img)
            cv2.waitKey(200)
            cv2.destroyAllWindows()
        '''
        x0, output = model1(data)
        #print x0.sum(0).size()
        #print data.sum(0).size()
        loss1=torch.norm((x0.sum(0)-data.sum(0))/(data.size()[0]), 2)
        loss2=torch.norm(x0-data,2)
        loss = loss2+F.nll_loss(output, target)+F.hinge_embedding_loss(data, target)

        pred = output.data.max(1)[1]  # get the index of the max log-probability
        n += pred.eq(target.data).cpu().sum()
        optimizer1.zero_grad()
        loss.backward()
        # print (data.grad)
        optimizer1.step()

    print ('Train loss accuracy is {}'.format(n / len(test_loader.dataset)))
    return n / len(test_loader.dataset)


if __name__=='__main__':
    '''
    model = classifier().cuda()
    # model=fc()
    optimizer = optim.Adam(model.parameters(), lr=0.01, betas=(0.9, 0.999), weight_decay=1e-3)

    acc = []
    acc = np.asarray(acc, np.float)
    for epoch in range(5):
        a = test_train(epoch)
        acc = np.append(acc, epoch)
        acc = np.append(acc, a)
    torch.save(model, '/home/hankeji/Desktop/new_model/ori_sourec_m.pkl')
    acc=np.reshape(acc, (-1,2))

    if os.path.exists('home/hankeji/Desktop/ADDA/'):
        np.save('home/hankeji/Desktop/ADDA/classifer.npy', acc)
    else:
        os.makedirs('home/hankeji/Desktop/ADDA/')
        np.save('home/hankeji/Desktop/ADDA/classifer.npy', acc)
    
    '''
    model =sour_cls().cuda()
    model1= sour_cls().cuda()
    optimizer = optim.Adam(model.parameters(), lr=0.001, betas=(0.9, 0.999), weight_decay=1e-4)
    #optimizer = optim.RMSprop(model.parameters(), lr=1e-3)
    optimizer1 = optim.Adam(model1.parameters(), lr=0.001, betas=(0.9, 0.999), weight_decay=1e-3)
    acc0 = []
    acc0 = np.asarray(acc0, np.float)
    for epoch in range(I_n):
        a = test_train(epoch)
        b=test_loss(epoch)
        acc0 = np.append(acc0, epoch)
        acc0 = np.append(acc0, a)
        acc0 = np.append(acc0, b)
    torch.save(model1, model_pth)
    acc0 = np.reshape(acc0, (-1, 3))

    if os.path.exists('home/hankeji/Desktop/ADDA/'):
        np.save('./data/sour_cls.npy', acc0)
    else:
        os.makedirs('home/hankeji/Desktop/ADDA/')
        np.save('./data/sour_cls.npy', acc0)
    '''
    import matplotlib.pyplot as plt
    from pylab import *
    plt1,=plt.plot(acc0[:, 0], acc0[:, 1], 'b', label='ori')
    plt2, =plt.plot(acc0[:, 0], acc0[:, 2], 'k', label='loss')

    plt.legend(handles=[plt1, plt2])
    leg = plt.gca().get_legend()
    leg_text = leg.get_texts()
    plt.setp(leg_text, fontsize=15, fontweight='bold')
    plt.xlabel('$\phi$ (epoch)', fontsize=15)
    plt.ylabel('accuracy of model', fontsize=15)
    ax = plt.axes()
    plt.show()
    '''


    #execfile('/home/hankeji/Desktop/papercode/ADDA/framwork.py')