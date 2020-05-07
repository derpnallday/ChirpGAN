import os
import numpy as np
from PIL import Image

WIDTH = 600
HEIGHT = 256

# seed for reproducibility
SEED = 42

class Dataset:

    def __init__(self, data_dir):

        scalograms = self.load_scal(data_dir)

        std_scalograms = self.standardize(scalograms)

        calls = [self.extract_calls(s, WIDTH) for s in std_scalograms]

        print('number of calls %d' % len(calls))

        forcedWidthCalls = self.forceWidth(calls, WIDTH)

        X = self.make_dataset(forcedWidthCalls, std_scalograms)

        X = X.reshape((-1,HEIGHT,WIDTH,1))

        print('dataset size: %d' % X.shape[0])

        self.save_dataset(X, os.path.join(data_dir, '../bird_data'))


    ###########################
    ### DATA PRE-PROCESSING ###
    ###########################

    def load_scal(self, data_dir):
        """loads scalograms from specified directory

        Args:
            data_dir - user specified directory where scalograms are saved

        Returns:
            scal - list of scalograms
        """
        images = []
        # append images to list
        for filename in sorted(os.listdir(data_dir)):
            if filename.endswith(".png"):
                img = Image.open(os.path.join(data_dir, filename))
                images.append(img)
                print(filename)
        
        # convert images to np array
        scal = [np.array(img) for img in images]
        
        return scal

    # type cast to float32
    # standardize to mean +- 3 std and clip
    def standardize(self, scalograms):
        """standardizes the given scalograms by type casting to float32, 
        standardizing, and clipping to +- 3 std

        Args:
            scalograms - list of scalograms

        Returns:
            scalograms - list of standardized scalograms
        """
        scalograms = [s.astype(np.float32) for s in scalograms] # type cast to np.float32
        scalograms = [(s - np.mean(s)) / np.std(s) for s in scalograms] # standardize
        scalograms = [np.clip(s, np.mean(s) - 3*np.std(s), np.mean(s) + 3*np.std(s)) for s in scalograms] # clip 
        
        for s in scalograms: # print info
            print('min: %f, max: %f, mean: %f, std: %f' % (np.min(s), np.max(s), np.mean(s), np.std(s))) 
            
        return scalograms

    #######################
    ### CALL EXTRACTION ###
    #######################

    def silent(self, m, arr):
        """returns whether given array is "silent"

        Args:
            m - the silence value
            arr - the array to determine if silent

        Returns:
            True if arr is silent, False otherwise
        """
        return np.all(np.isclose(arr, m))


    def extract_calls(self, scal, width):
        """extracts width length calls from scalogram scal

        Args:
            scal - specified scalogram to extract calls from
            width - width of the extracted calls

        Returns:
            calls - list of calls of length width in scal
        """
        m = np.min(scal)
        
        calls = []
        
        start = -1
        end = -1
        
        inCall = False
        
        for x in range(1,scal.shape[1]):
            if self.silent(m, scal[:,x]): # x silent
                if self.silent(m, scal[:,x-1]): # x-1 silent
                    if inCall:
                        if x - start >= width:
                            calls.append([start,end])
                            inCall = False
                            start = x - 1
                else: # x-1 not silent
                    end = x
            else: # x not silent
                if self.silent(m, scal[:,x-1]): # x-1 silent
                    if not inCall:
                        start = x - 1
                        inCall = True
                else: # x-1 not silent
                    if x - start >= width:
                        calls.append([start,x])
                        start = x - 1                
                        
        return calls

    def forceWidth(self, calls, width):
        forcedCalls = []
        
        for call in calls:
            tmp = []
            for [a,b] in call:
                diff = width - (b-a)
                a -= diff//2
                b += diff//2
                if diff%2!=0:
                    a -= 1
                
                tmp.append([a,b])
            
            forcedCalls.append(np.asarray(tmp))
        
        return np.asarray(forcedCalls)


    def plot_calls(self, scal, endpoints):
        """plots the calls in scal based on ranges specified by endpoints

        Args:
            scal - specified scalogram
            endpoints - list of (a,b) endpoints of a call 
        """
        x = int(math.sqrt(len(endpoints)))+1
        
        plt.figure(figsize=(100,100))
        
        for i,[a,b] in enumerate(endpoints):
            plt.subplot(x,x+1,i+1)
                    
            diff = 600 - (b-a)
            a -= diff//2
            b += diff//2
            if diff%2!=0:
                a -= 1
            
            plt.imshow(scal[:,a:b], cmap='inferno')
        
        plt.show()


    ###########################
    ### DATASET PREPARATION ###
    ###########################

    def make_dataset(self, frames, scalograms):
        """makes a dataset based on the given scalograms and corresponding frames

        Args:
            frames - list of frames that define the calls
            scalograms - list of scalograms

        Returns:
            dataset - np array of scalogram calls
        """
        
        assert len(frames) == len(scalograms)
        
        dataset = []
        
        for f,s in zip(frames, scalograms):
            for [a,b] in f:
                img = np.array(s[:, a:b])
                
                if not img.shape == (256,600):  # TODO: needs to be specified as parameter or config
                    continue
                
                dataset.append(img)
        
        dataset = np.array(dataset)
        
        return dataset

    def downscale(self, dataset, factor):
        """downscales the given dataset by the given factor

        Args:
            dataset - the dataset of images to downscale
            factor - the factor by which to downscale images

        Returns:
            result - dataset of images downscaled by specified factor
        """
        import skimage.measure
        
        # downscaling factor for each dimension
        assert len(factor) == (len(dataset.shape)-1)
        
        result = []
        
        scale_factor = tuple(2**f for f in factor)
        
        for frame in dataset:
            tmp = skimage.measure.block_reduce(frame, scale_factor, np.max)
            result.append(tmp)
            
        result = np.asarray(result)
        
        result = result.reshape((-1, result.shape[1], result.shape[2], 1))
        
        return result

    def save_dataset(self, dataset, filename):
        np.savez(filename, dataset)
