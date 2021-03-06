# -*- coding: utf-8 -*-
"""
Created on Wed Oct 17 14:44:01 2018

@author: ben
"""
import numpy as np
import h5py
import matplotlib.pyplot as plt
from ATL11.ATL06_data import ATL06_data
from smooth_corrected import smooth_corrected

the_dir= '/Volumes/ice2/ben/scf/AA_06/mat_h5_npz/'
files=glob.glob(the_dir+'/*.h5')
the_file=files[1]

#the_file=the_dir+'ATL06_20181016112019_02720111_mat_01.h5'
#'ATL06_20181017104659_02870110_200_01.h5'

beam_pair=1
#the_file='/Volumes/ice2/ben/scf/AA_06/mat_h5/ATL06_2018_10_02_00100110_944_01.h5'


# read the altimetry data using the ATL06_data object defined in the smithb/ATL11 repository
D6=ATL06_data(filename=the_file, beam_pair=beam_pair)
D6.h_li[D6.h_li>2.e4]=np.NaN
beam_names=['gt%d%s' %(beam_pair, b) for b in ['l','r']]

# define fields to read from the residual_histogram group
fields=['segment_id_list','count','bckgrd_expected','dh','pulse_count']
resImages=list()
resHists=list()
h5f=h5py.File(the_file)
# loop over beams in the pair
for beam_name in beam_names:
    # make a set of dictionaries that contain image information.  Each dictionary 
    # contains: an'extent' field, giving the location of the image in segment number and vertical
    #         : a 'count' field, which has the count data, with one column for every _possible_ segment center for a histogram, padded with NaNs
    #         : a 'count_norm' field, which corrects the counts for the number of segments actually used.
    resHist=dict()
    for field in fields:
        resHist[field]=np.array(h5f[beam_name]['residual_histogram'][field], dtype=np.float64)
    resHist['segment_id_list'][(resHist['segment_id_list']<1) | (resHist['segment_id_list']==2**31-1)]=np.NaN
    # find the segment number for the center of each histogram bin
    seg0=0.5*(np.nanmin(resHist['segment_id_list'], axis=1)+np.nanmax(resHist['segment_id_list'], axis=1))
    # fill in gaps with NaNs
    seg0[seg0==-1]=np.NaN
    vert_res=np.diff(resHist['dh'][0:2])
    res_img=dict()
    # set up empty arrays
    res_img['seg_ctr']=np.arange(5*np.floor(np.nanmin(seg0)/5), np.nanmax(seg0), 10)
    res_img['bckgrd_expected']=np.zeros_like(res_img['seg_ctr'])+np.NaN
    res_img['bckgrd_norm']=np.zeros_like(res_img['seg_ctr'])+np.NaN

    res_img['count']=np.zeros([resHist['dh'].size, res_img['seg_ctr'].size])+np.NaN    
    res_img['count_norm']=np.zeros([resHist['dh'].size, res_img['seg_ctr'].size])+np.NaN
    for col_in, this_seg in enumerate(seg0):
        # find the segment number in the 'count' array that's closest to the histogram bin center, write the histogram info into it
        col_out=np.argmin(np.abs(res_img['seg_ctr']-this_seg))
        res_img['count'][:, col_out]=resHist['count'][col_in,:]
        res_img['count_norm'][:, col_out]=resHist['count'][col_in,:]/resHist['pulse_count'][col_in]
        #res_img['bkgrd_expected'][col_out]=resHist['bkgrd_expected'][col_in,0]
        res_img['bckgrd_norm'][col_out]=resHist['bckgrd_expected'][col_in]/resHist['pulse_count'][col_in]
    res_img['extent']=[res_img['seg_ctr'][0]-2.5, res_img['seg_ctr'][-1]-2.5, resHist['dh'][0]-vert_res/2, resHist['dh'][-1]-vert_res/2]
    resHists.append(resHist)
    resImages.append(res_img)
    
h5f.close() 


ax=list()
hi=list()
plt.figure(1); plt.clf()
ax.append(plt.subplot(3, 1, 1))
plt.plot(D6.segment_id, D6.h_li)
plt.ylabel('height, m');
for ii in [0, 1]:
    ax.append(plt.subplot(3, 1, ii+2, sharex=ax[0]))
    #hi.append(plt.imshow(np.log10(smooth_corrected(resImages[ii]['count_norm'], [2, 2])+0.001), extent=resImages[ii]['extent'], origin='lower'))
    hi.append(plt.imshow(np.log10(resImages[ii]['count_norm']+0.001), extent=resImages[ii]['extent'], origin='lower'))

    ax[-1].set_aspect('auto')
    ax[-1].set_ylim([-5, 5])
    plt.ylabel('height WRT surface')
    #plt.colorbar()
plt.xlabel('segment_id')    

plt.figure(2); plt.clf()
ax2=list()
for ii in [0, 1]:
    ax2.append(plt.subplot(2,1,ii+1))
    plt.plot(resImages[ii]['seg_ctr'], np.mean(resImages[ii]['count_norm'][100:250,:]*500, axis=0),'r.')
    plt.plot(resImages[ii]['seg_ctr'], resImages[ii]['bckgrd_norm']*500,'b.' )
    
    